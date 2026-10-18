#!/usr/bin/env python3
"""VIVE Flow compatibility patch. Requires user-provided original APK.
Python 3.9+, Java Android build-tools apksigner, and user's own signing key.
No original HTC APK content is bundled.
"""
import argparse, copy, hashlib, io, json, os, pathlib, subprocess, tempfile, zipfile, zlib

PATCHES_FILE = pathlib.Path(__file__).resolve().parent / 'patches' / 'changes.json'
PATCHES = json.loads(PATCHES_FILE.read_text(encoding='utf-8'))['patches']

ORIGINAL_MANIFEST_SHA256 = '72d20668b5544f6409c791ff06a84329fdee7a998b232b0d35ca045b56e9a11f'

def apply_spans(data, spans, label):
    out = bytearray(data)
    for span in spans:
        offset = span['offset']
        size = span['original_length']
        replacement = bytes.fromhex(span['replacement_hex'])
        if len(replacement) != size or offset < 0 or offset + size > len(out):
            raise ValueError(f'{label}: invalid patch span at {offset}')
        current = bytes(out[offset:offset + size])
        if hashlib.sha256(current).hexdigest() != span['original_sha256']:
            raise ValueError(f'{label}: original bytes mismatch at {offset}; unsupported APK version')
        out[offset:offset + size] = replacement
    return bytes(out)

def repack(source, replacements, output):
    with zipfile.ZipFile(source) as inp, zipfile.ZipFile(output, 'w') as out:
        for info in inp.infolist():
            if info.filename.upper().startswith('META-INF/') and info.filename.upper().endswith(('.RSA','.DSA','.EC','.SF','.MF')):
                continue
            payload = replacements.get(info.filename)
            if payload is None: payload = inp.read(info.filename)
            out.writestr(info, payload)

def sign(apksigner, unsigned, signed, keystore, alias, password):
    cmd = [apksigner, 'sign', '--ks', str(keystore), '--ks-key-alias', alias,
           '--ks-pass', 'pass:' + password, '--out', str(signed), str(unsigned)]
    subprocess.run(cmd, check=True)
    subprocess.run([apksigner, 'verify', str(signed)], check=True)

def main():
    p = argparse.ArgumentParser(description='Patch a user-supplied original VIVE Business Streaming APK for VIVE Flow')
    p.add_argument('original_apk', type=pathlib.Path)
    p.add_argument('--output', type=pathlib.Path, default=pathlib.Path('Vive_Flow_FOCUS3_patched.apk'))
    p.add_argument('--apksigner', default='apksigner')
    p.add_argument('--keystore', type=pathlib.Path, required=True)
    p.add_argument('--alias', required=True)
    p.add_argument('--ks-pass-env', default='APK_KEYSTORE_PASSWORD')
    args = p.parse_args()
    password = os.environ.get(args.ks_pass_env)
    if not password: p.error('Set environment variable ' + args.ks_pass_env + ' with keystore password')
    if not args.original_apk.is_file(): p.error('Original APK not found')
    with zipfile.ZipFile(args.original_apk) as src:
        manifest = src.read('AndroidManifest.xml')
        if hashlib.sha256(manifest).hexdigest() != ORIGINAL_MANIFEST_SHA256:
            p.error('Unsupported original APK version (manifest checksum differs). Use matching official release.')
        new_manifest = apply_spans(manifest, PATCHES['AndroidManifest.xml'], 'AndroidManifest.xml')
        native_name = 'lib/arm64-v8a/libnative-wvr-jni.so'
        new_native = apply_spans(src.read(native_name), PATCHES[native_name], native_name)
        cfg = json.loads(src.read('assets/HmdList.json'))
        if any(d.get('HMD') == 'htc_hue' for d in cfg['Device']):
            p.error('APK already contains htc_hue configuration; expected unmodified original')
        default = next(d for d in cfg['Device'] if d.get('HMD') == 'DEFAULT')
        flow = copy.deepcopy(default); flow['HMD'] = 'htc_hue'
        cfg['Device'].insert(0, flow)
        new_cfg = json.dumps(cfg, indent=4, ensure_ascii=False).encode('utf-8')
        nested_bytes = src.read('assets/wavevr/client-module.apk')
    with zipfile.ZipFile(io.BytesIO(nested_bytes)) as nested:
        dex = bytearray(apply_spans(nested.read('classes.dex'), PATCHES['nested_classes'], 'nested classes.dex'))
    # DEX signature (SHA-1 bytes 12..31) and Adler-32 checksum (bytes 8..11)
    dex[12:32] = hashlib.sha1(dex[32:]).digest()
    dex[8:12] = (zlib.adler32(dex[12:]) & 0xffffffff).to_bytes(4, 'little')
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        nested_unsigned = td/'nested-unsigned.apk'
        nested_signed = td/'nested-signed.apk'
        outer_unsigned = td/'outer-unsigned.apk'
        repack(io.BytesIO(nested_bytes), {'classes.dex': bytes(dex)}, nested_unsigned)
        sign(args.apksigner, nested_unsigned, nested_signed, args.keystore, args.alias, password)
        repack(args.original_apk, {'AndroidManifest.xml':new_manifest, native_name:new_native,
               'assets/HmdList.json':new_cfg, 'assets/wavevr/client-module.apk':nested_signed.read_bytes()}, outer_unsigned)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        sign(args.apksigner, outer_unsigned, args.output, args.keystore, args.alias, password)
    print('Created:', args.output)
    print('Note: not tested on hardware; signing key differs from HTC official release.')

if __name__ == '__main__': main()
