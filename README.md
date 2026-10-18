# VIVE Flow Business Streaming compatibility patch

非公式・非公認の **VIVE Flow向けVIVE Business Streaming互換性パッチ**です。HTC/VIVEとは無関係です。利用者自身が正規に入手した**対応する純正APK**をローカルで修正します。**本リポジトリには純正APKや改造済みAPKを同梱しません。**

## 動作確認

報告された実機検証環境：**VIVE Flow / Android 9 (API 28) / Wi-Fi / VIVE Hub 2.3.3b / SteamVR**。PC VR映像表示、**6DoF**、**ハンドトラッキング**の動作が確認されています。ほかのVIVE Hubバージョンやゲームとの互換性は未確認です。これは動作報告であり、`patch.py` の出力APKを全環境で検証したことを意味しません。

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
D:\steam\steamapps\common\VIVE HUB\VIVE Business Streaming\RRClient\Vive_rrClient.apk
```

**Steamライブラリのインストール先が異なる場合は、パスの先頭部分を読み替えてください。** このAPKを自分の作業フォルダーにコピーしてからパッチを実行します。純正APK自体を本リポジトリから配布することはありません。

## 使い方（Windows / PowerShell）

VIVE Hubに付属する純正APKを使い、VIVE Flow用のAPKを作成してインストールします。

### STEP 1：作業フォルダーを準備する

デスクトップなどに `ViveFlowPatch` フォルダーを作成してください。

GitHubから取得した `patch.py` と `patches` フォルダー、VIVE Hubからコピーした `Vive_rrClient.apk` を配置します。

```text
ViveFlowPatch/
├── patch.py
├── Vive_rrClient.apk
└── patches/
    └── changes.json
```

`changes.json` は必ず `patches` フォルダー内に配置してください。

### STEP 2：PowerShellを開く

エクスプローラーで `ViveFlowPatch` フォルダーを開き、アドレスバーに `powershell` と入力してEnterキーを押してください。

以下のコマンドでファイルを確認します。

```powershell
Get-ChildItem
Get-ChildItem .\patches
```

`patch.py`、`Vive_rrClient.apk`、`changes.json` が表示されれば準備完了です。

### STEP 3：APK署名用の鍵を作成する（初回のみ）

純正APKを変更すると元の署名が無効になるため、自分専用の署名鍵を作成します。

```powershell
keytool -genkeypair -keystore .\viveflow.keystore -alias viveflow -keyalg RSA -keysize 3072 -validity 10000
```

実行すると、署名鍵のパスワードと証明書情報の入力を求められます。

#### `keytool` で質問される項目

| 質問 | 意味 | 入力例 |
|---|---|---|
| 姓名（CN） | 証明書の識別名 | `ViveFlowPatch` |
| 組織単位名（OU） | 部署・グループ名 | `Personal` |
| 組織名（O） | 組織・プロジェクト名 | `PersonalProject` |
| 都市名または地域名（L） | 市区町村など | `Tokyo` |
| 都道府県名または州名（ST） | 都道府県など | `Tokyo` |
| 2文字の国コード（C） | 国コード | `JP` |

これらはAPKの署名証明書に記録される情報です。HTCアカウントの情報ではありません。

証明書の情報は第三者が確認できるため、個人情報の入力には注意してください。

最後に、次のような確認画面が表示されます。

```text
CN=ViveFlowPatch, OU=Personal, O=PersonalProject, L=Tokyo, ST=Tokyo, C=JPでよろしいですか。
  [いいえ]:
```

`[いいえ]` はエラーではありません。Enterキーだけを押すと、最初の質問に戻ります。

入力内容に問題がなければ、日本語環境では次のように入力してください。

```text
  [いいえ]: はい
```

※ Javaのバージョンや言語設定によって、受け付けられる確認文字列が異なる場合があります。

**日本の国コードは `80` ではなく `JP` です。**

完了すると、作業フォルダーに `viveflow.keystore` が作成されます。

**署名鍵とパスワードはGitHubに公開しないでください。**

### STEP 4：署名鍵のパスワードを設定する

STEP 3で作成した署名鍵のパスワードを、PowerShellの環境変数に設定します。

以下のコマンドを実行してください。

```powershell
$env:APK_KEYSTORE_PASSWORD = Read-Host "Keystore password"
```

パスワードを聞かれたら、署名鍵を作成したときのパスワードを入力してEnterキーを押します。

**注意：** この方法では入力したパスワードが画面に表示されます。周囲に注意してください。

パスワードを環境変数に設定するのは、`patch.py` がAPKの署名を行う際に使用するためです。

### STEP 5：純正APKにパッチを適用する

同じPowerShell画面で、次のコマンドを実行します。

```powershell
python .\patch.py .\Vive_rrClient.apk --output .\Vive_Flow_FOCUS3_patched.apk --keystore .\viveflow.keystore --alias viveflow
```

このコマンドは以下の処理を行います。

1. 純正APKが対応バージョンか確認する
2. Android 9向けの互換性修正を適用する
3. VIVE Flow向けの機種識別処理を変更する
4. 修正済みAPKを署名する
5. 出力先にAPKを保存する

正常に完了すると、作業フォルダーに次のファイルが作成されます。

```text
Vive_Flow_FOCUS3_patched.apk
```

これがVIVE FlowにインストールするAPKです。

#### `apksigner` が見つからない場合

Android SDK Build-Tools内の `apksigner.bat` をフルパスで指定してください。

例えば、以下の場所にインストールされている場合です。

```text
C:\Users\Owner\AppData\Local\Android\Sdk\build-tools\34.0.0\apksigner.bat
```

実行例：

```powershell
python .\patch.py .\Vive_rrClient.apk --output .\Vive_Flow_FOCUS3_patched.apk --keystore .\viveflow.keystore --alias viveflow --apksigner "C:\Users\Owner\AppData\Local\Android\Sdk\build-tools\34.0.0\apksigner.bat"
```


#### パッチが途中で停止した場合

純正APKのバージョンが一致しない、必要なツールが見つからない、署名鍵のパスワードが間違っているなどの原因が考えられます。

表示されたエラーメッセージを確認してください。

**対応していない純正APKに対して、強制的にパッチを適用しないでください。**

### STEP 6：VIVE FlowをPCに接続する

USBデバックを有効にしてPCにUSB接続します。
ファイルの転送を押すと内部ストレージが現れるのでダウンロードフォルダにAPKをコピーしVIVEFlowからインストールしてください。

以下はコマンドでの方法です。

VIVE FlowでUSBデバッグを利用できる状態にして、USBケーブルでWindows PCに接続します。

PowerShellで次のコマンドを実行してください。

```powershell
adb devices
```

正常に認識されると、次のような表示になります。

```text
List of devices attached
XXXXXXXX    device
```

`XXXXXXXX` の部分は接続したデバイスによって異なります。

`unauthorized` と表示される場合は、VIVE Flow側でUSBデバッグを許可してください。

デバイスが表示されない場合は、USBケーブル、ドライバー、USBデバッグ設定を確認してください。

### STEP 7：改造APKをインストールする

STEP 5で作成したAPKをVIVE Flowにインストールします。

```powershell
adb install .\Vive_Flow_FOCUS3_patched.apk
```

次のように表示されれば成功です。

```text
Success
```

#### `INSTALL_FAILED_UPDATE_INCOMPATIBLE` が表示された場合

既存のアプリと、今回作成したAPKの署名が異なる可能性があります。

その場合は、既存アプリをアンインストールしてからインストールし直します。

**注意：アンインストールすると、既存アプリの設定やデータが削除される場合があります。**

問題ないことを確認してから実行してください。

```powershell
adb uninstall com.htc.vive.vstreaming
```

続いて、再度インストールします。

```powershell
adb install .\Vive_Flow_FOCUS3_patched.apk
```

### STEP 8：オーバーレイ権限を設定する

VIVE Flowでは、アプリ内の権限確認画面を正常に操作できない場合があります。

その場合はADBを使用して権限を設定します。

```powershell
adb shell appops set com.htc.vive.vstreaming SYSTEM_ALERT_WINDOW allow
```

エラーが表示されなければ設定完了です。

このコマンドは、VIVE Business Streamingが他のアプリの上に画面を表示するための権限を許可するものです。

### STEP 9：VIVE Hubに接続する

APKのインストールと権限設定が完了したら、PC VR接続を行います。

1. Windows PCで **VIVE Hub 2.3.3b** を起動します。
2. PCとVIVE Flowを同じネットワークに接続します。
3. VIVE FlowでVIVE Business Streamingアプリを起動します。
4. アプリに表示されたPCを選択します。
5. Wi-Fi接続が確立するまで待ちます。
6. SteamVRの映像が表示されれば接続成功です。

VIVEHubおすすめの設定
ビットレート　お好み
ストリーミンググラフィックの設定　品質
ハンドトラッキングを利用する場合　入力→トラッキング→ハンドトラッキングを有効にする（精度はかなり悪い）

開発時の改造APKでは、以下の動作が確認されています。

- PC VR映像表示
- マイク
- スピーカー
- 6DoFトラッキング
- ハンドトラッキング

**動作確認環境はVIVE Hub 2.3.3bです。** その他のバージョンやすべてのSteamVRゲームでの動作は保証していません。

---

### よくある問題

| 症状 | 対処方法 |
|---|---|
| `python` が認識されない | PythonのインストールとPATH設定を確認してください。 |
| `keytool` が認識されない | Java JDKのインストールとPATH設定を確認してください。 |
| `apksigner` が見つからない | `--apksigner` で `apksigner.bat` のフルパスを指定してください。 |
| パッチが適用できない | 対応するバージョンの純正APKを使用してください。 |
| `adb devices` にVIVE Flowが表示されない | USB接続、ドライバー、USBデバッグの許可を確認してください。 |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | 既存アプリと署名が異なる可能性があります。 |
| オーバーレイ権限を許可できない | STEP 8のADBコマンドを実行してください。 |
| 接続先PCが表示されない | PCとFlowのネットワーク、ファイアウォール、VIVE Hubの起動状態を確認してください。 |
| SteamVR映像が表示されない | VIVE HubとSteamVRを再起動し、接続状態を確認してください。 |

**注意：** `patch.py` から生成したAPKの実機動作については、公開前に別途確認が必要です。


## 注意・免責

**利用は完全に自己責任です。** 作者は、利用に伴うデバイスの不具合、データ損失、接続障害、セキュリティ問題、その他の損害について、適用法で認められる最大限の範囲で責任を負いません。**現状有姿（AS IS）**で提供し、動作保証・サポート保証はありません。使用者は適用法令と純正ソフトウェアのライセンス条件を確認してください。

## ライセンス

このリポジトリで新たに作成した `patch.py` とパッチ定義・説明文には、同梱のMIT Licenseを適用します。**HTC/VIVEの純正APK・ライブラリ・商標等に対して権利を付与するものではありません。**
