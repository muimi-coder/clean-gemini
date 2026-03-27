# 🧹 お掃除エージェント - Gemini Context Cleaner

## 🚀 プロジェクトの目的
このプロジェクトは、AI（Gemini）との対話ログを効率的に管理し、作業環境を常に清潔に保つために開発されました。

### 📋 背景と課題
* **ログの集約**: Geminiとの膨大な会話ログ（AIExporter経由）を1箇所にまとめるため、Chromeのデフォルト保存先をGoogle Drive上の特定フォルダに設定。
* **副作用**: Chrome経由でダウンロードするアプリのインストーラー（.dmg, .pkg）や圧縮ファイル（.zip）まで同じフォルダに混入し、管理が煩雑になる課題が発生。

### 💡 解決策
Pythonの `watchdog` ライブラリを使用した常駐型エージェント。
指定フォルダをリアルタイム監視し、特定の拡張子を持つファイルが置かれた瞬間に、ローカルの `Downloads` フォルダへ「シュンッ！」と自動移動させます。

## 🛠️ 技術スタック
- **Language**: Python 3.9+
- **Library**: watchdog (イベント駆動型ファイルシステム監視)
- **Infrastructure**: Mac mini (24/7 稼働の司令塔)
- **Management**: GitHub (Mac mini / MBP の設定同期)

## 🏗️ D-Twin（デジタルツイン）構成
- **Mac mini**: 本体の「脳」として常時稼働し、クラウド経由で全デバイスのフォルダを清掃。
- **MacBook Pro**: GitHubからコードをクローンし、必要に応じてローカルでも同等のエージェントを稼働可能。

---

## セットアップ手順

### 1. 必要なライブラリをインストール
```bash
pip install -r requirements.txt
```

### 2. パスの設定

[clean_gemini_improved.py](clean_gemini_improved.py) は環境変数 `CLEAN_GEMINI_TARGET_DIR` を優先的に読み込みます。

**方法A：環境変数で設定（推奨）**

```bash
export CLEAN_GEMINI_TARGET_DIR="~/Library/CloudStorage/GoogleDrive-[あなたのメール]/マイドライブ/My_Context_Bank_2026/XX_Gemini_Context"
```

その後、スクリプトを実行：
```bash
python clean_gemini_improved.py
```

**方法B：`.env` ファイルで設定**

`.env` ファイルをプロジェクトディレクトリに作成：
```bash
# .env
CLEAN_GEMINI_TARGET_DIR="/Users/[username]/Library/CloudStorage/GoogleDrive-[あなたのメール]/マイドライブ/My_Context_Bank_2026/XX_Gemini_Context"
```

> ⚠️ `.env` ファイルは `.gitignore` に追加して、GitHub にアップロードされないようにしてください

**方法C：デフォルトパス（フォルダがワイルドカード対応の場合）**

Google Drive フォルダの名前パターンが統一していれば、自動検出が可能です。詳しくはコード内のコメントを参照。

> 💡 **推奨**: 各マシンで環境変数を一度設定すれば、以降は自動で認識されます

---

## 実行方法

### 手動実行
```bash
python clean_gemini_improved.py
```

### Mac mini：バックグラウンドで常時実行（推奨）

**launchd を使った自動起動設定**

1. 設定ファイルを作成：
```bash
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/com.local.clean-gemini.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.local.clean-gemini</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/takachan/Library/CloudStorage/GoogleDrive-.../clean_gemini_improved.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/clean_gemini.out</string>
    <key>StandardErrorPath</key>
    <string>/tmp/clean_gemini.err</string>
</dict>
</plist>
EOF
```

> ⚠️ `ProgramArguments` の Python パスとスクリプトパスを実際の位置に変更してください

2. 登録して起動：
```bash
launchctl load ~/Library/LaunchAgents/com.local.clean-gemini.plist
launchctl start com.local.clean-gemini
```

3. 動作確認：
```bash
launchctl list | grep clean-gemini
```

---

## ログ確認

すべてのアクション（移動完了、エラーなど）は以下に記録：
```bash
~/.clean_gemini/clean_gemini.log
```

リアルタイム確認：
```bash
tail -f ~/.clean_gemini/clean_gemini.log
```

---

## 機能

✅ **ファイルシステム監視** → ポーリング不要、実時間反応  
✅ **安全なファイル移動** → 重複時は自動リネーム（タイムスタンプ追加）  
✅ **詳細ログ** → すべての動作を記録  
✅ **汎用的な設定** → 複数Macで独立して動作可能  
✅ **ダウンロード中ファイルスキップ** → .tmp/.crdownload を処理対象外に  

---

## 設定のカスタマイズ

### 監視対象の拡張子を追加
```python
TRASH_EXTENSIONS = {".dmg", ".pkg", ".zip", ".exe", ".iso", ".rar", ".7z"}
```

### 移動先を変更
```python
DEST_DIR = os.path.expanduser("~/Desktop")  # 例：デスクトップに移動
```

---

## トラブルシューティング

### 「フォルダが見つかりません」エラー
- `TARGET_DIR` のパスが正しいか確認
- Google Drive フォルダが同期されているか確認

### ファイルが移動されない
- ターミナルで直接実行して、ログを確認：
  ```bash
  python clean_gemini_improved.py
  ```
- フォルダのアクセス権限を確認：
  ```bash
  ls -la ~/Google\ Drive/...
  ```

### CPU使用率が高い
- watchdog のバックエンド設定を確認
- [watchdog ドキュメント](https://watchdog.readthedocs.io/) 参照

---

## GitHub での共有方法（推奨）

1. GitHub にリポジトリ作成
2. ファイル追加：
   - `clean_gemini_improved.py`
   - `requirements.txt`
   - `README.md`
   - `.gitignore`（ログは除外）

3. 各マシンでクローン：
   ```bash
   git clone https://github.com/[username]/clean-gemini.git
   cd clean-gemini
   pip install -r requirements.txt
   python clean_gemini_improved.py
   ```

4. 設定の共有：
   - 各マシンで `TARGET_DIR` を局所的に編集
   - パーソナル部分は `.gitignore` で除外

---

## ライセンス
個人用スクリプト

---

## 改善履歴

**v2.0（新版）**
- ✨ watchdog ライブラリで ファイルシステムイベント監視に切り替え（ポーリング方式から改善）
- ✨ ログ機能追加（~/.clean_gemini/clean_gemini.log）
- ✨ 重複ファイル対応（タイムスタンプで自動リネーム）
- ✨ ダウンロード中ファイルスキップ（.tmp/.crdownload）
- ✨ 詳細なエラー分類処理
- ✨ launchd による Mac mini での常時稼働設定
- ✨ GitHub での複数マシン対応設定

**v1.0（旧版）**
- 10秒おきのポーリング方式（見守り続ける方式、電力効率が低い）
