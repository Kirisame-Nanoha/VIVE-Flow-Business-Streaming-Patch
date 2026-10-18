# VIVE Flow Business Streaming compatibility patch

非公式・非公認の **VIVE Flow向けVIVE Business Streaming互換性パッチ**です。HTC/VIVEとは無関係です。利用者自身が正規に入手した**対応する純正APK**をローカルで修正します。**本リポジトリには純正APKや改造済みAPKを同梱しません。**

## 動作確認

報告された実機検証環境：**VIVE Flow / Android 9 (API 28) / Wi-Fi / VIVE Hub 2.3.3b / SteamVR**。PC VR映像表示、**マイク**、**スピーカー**、**6DoF**、**ハンドトラッキング**の動作が確認されています。ほかのVIVE Hubバージョンやゲームとの互換性は未確認です。これは動作報告であり、`patch.py` の出力APKを全環境で検証したことを意味しません。

## 純正アプリとの違い

| 対象 | 変更点 | 目的 |
|---|---|---|
| `AndroidManifest.xml` | `minSdkVersion` をAPI 29からAPI 28に変更 | Android 9でのインストール |
| `assets/wavevr/client-module.apk` 内 `classes.dex` | Android 10以降のライフサイクルAPI呼び出し箇所を修正しDEXの署名・チェックサムを再計算 | Android 9での起動時クラッシュ回避 |
| `assets/HmdList.json` | `DEFAULT` を基に `htc_hue` の機種エントリを追加 | Flowのクライアント側認識 |
| `lib/arm64-v8a/libnative-wvr-jni.so` | `getValidHmdType()` に関係する識別処理をFocus 3向けに修正 | PC側で `OTHER` と判定される接続拒否の回避 |
| APK署名 | 内側・外側のAPKを利用者自身の鍵で再署名 | 修正済みAPKのインストール |

PC側の `HmdList.json` やVIVE Hub実行ファイルの変更は不要です。なお、パッチは機種識別を変更するもので、実際のFlowのハードウェア性能をFocus 3に変えるものではありません。

## 必要なもの

- Python 3.9以降（標準ライブラリのみ）
- Android SDK Build-Tools の `apksigner` とJavaの `keytool`
- 利用者が正規に入手した**対応する純正VIVE Business Streaming APK**（パッチは原本のマニフェストSHA-256を照合し、異なるバージョンを拒否します）
- Windows PC、ADB、VIVE Flow

## 純正APKの入手方法

Windows PCに **VIVE Hub 2.3.3b** をインストールすると、VIVE Business Streamingの純正APKを次の場所から取得できます（Steamライブラリを `D:\steam` にインストールした場合）。

```text
\steam\steamapps\common\VIVE HUB\VIVE Business Streaming\RRClient\Vive_rrClient.apk
```

**Steamライブラリのインストール先が異なる場合は、パスの先頭部分を読み替えてください。** このAPKを自分の作業フォルダーにコピーしてからパッチを実行します。純正APK自体を本リポジトリから配布することはありません。

## 使い方（PowerShell）

`patch.py` と `patches/changes.json` のフォルダー構成を維持し、上記の場所からコピーした純正APKを `patch.py` と同じ作業フォルダーに配置します。最初に自分専用の署名鍵を生成します。

```powershell
keytool -genkeypair -keystore .\viveflow.keystore -alias viveflow -keyalg RSA -keysize 3072 -validity 10000
```

```powershell
$env:APK_KEYSTORE_PASSWORD = Read-Host 'Keystore password'
python .\patch.py .\Vive_rrClient.apk --output .\Vive_Flow_FOCUS3_patched.apk --keystore .\viveflow.keystore --alias viveflow
```

`apksigner` がPATHにない場合は `--apksigner 'C:\Android\Sdk\build-tools\<version>\apksigner.bat'` のように指定してください。Windows環境によっては `apksigner.bat` をフルパスで指定する必要があります。

既存アプリと署名が異なる場合、**設定やデータの消失に注意**してから旧アプリをアンインストールします。

```powershell
adb uninstall com.htc.vive.vstreaming
adb install .\Vive_Flow_FOCUS3_patched.apk
adb shell appops set com.htc.vive.vstreaming SYSTEM_ALERT_WINDOW allow
```

VIVE Hub 2.3.3bを起動し、FlowからWi-Fi接続してください。APKの再署名により純正APKの上書き更新はできない場合があります。

## `patches/` の内容

`changes.json` は変更位置、原本の短い領域のSHA-256、差し替えバイト列を記録する**機械可読パッチ定義**です。原本のAPK、ライブラリ、DEXファイル全体は含みません。純正アプリの権利はHTC等の権利者に帰属します。差分形式であっても法的リスクがなくなるわけではありません。

## 注意・免責

**利用は完全に自己責任です。** 作者は、利用に伴うデバイスの不具合、データ損失、接続障害、セキュリティ問題、その他の損害について、適用法で認められる最大限の範囲で責任を負いません。**現状有姿（AS IS）**で提供し、動作保証・サポート保証はありません。使用者は適用法令と純正ソフトウェアのライセンス条件を確認してください。

## ライセンス

このリポジトリで新たに作成した `patch.py` とパッチ定義・説明文には、同梱のMIT Licenseを適用します。**HTC/VIVEの純正APK・ライブラリ・商標等に対して権利を付与するものではありません。**
