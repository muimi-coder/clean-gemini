import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ==================== 設定 ====================
# 監視対象フォルダ（各マシンで編集してください）
# 優先順位: 環境変数 > デフォルトパス
TARGET_DIR = os.getenv(
    "CLEAN_GEMINI_TARGET_DIR",
    os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/マイドライブ/My_Context_Bank_2026/XX_Gemini_Context")
)

# 移動先フォルダ
DEST_DIR = os.path.expanduser("~/Downloads")

# 追い出したい拡張子
TRASH_EXTENSIONS = {".dmg", ".pkg", ".zip", ".exe", ".iso", ".app", ".nosync", ".tar", ".bz2", ".7z", ".dSYM"}

# ログファイル
LOG_DIR = os.path.expanduser("~/.clean_gemini")
LOG_FILE = os.path.join(LOG_DIR, "clean_gemini.log")

# ==================== ロギング設定 ====================
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ==================== ユーティリティ関数 ====================
def ensure_dest_dir_exists():
    """移動先フォルダが存在することを確認"""
    if not os.path.exists(DEST_DIR):
        try:
            os.makedirs(DEST_DIR, exist_ok=True)
            logger.info(f"移動先フォルダを作成: {DEST_DIR}")
        except Exception as e:
            logger.error(f"移動先フォルダ作成失敗: {e}")
            return False
    return True


def is_valid_target_file(filepath):
    """ファイルが処理対象かどうかを判定"""
    # 通常ファイルであることを確認
    if not os.path.isfile(filepath):
        return False

    # ダウンロード中のファイルをスキップ（.tmp, .crdownload など）
    filename = os.path.basename(filepath)
    if filename.startswith("."):
        return False
    if filename.endswith((".tmp", ".crdownload", ".part")):
        return False

    # 対象拡張子かどうかを確認
    _, ext = os.path.splitext(filename)
    return ext.lower() in TRASH_EXTENSIONS


def move_file_safely(src_path, dest_dir):
    """ファイルを安全に移動（重複対応）"""
    try:
        filename = os.path.basename(src_path)
        dest_path = os.path.join(dest_dir, filename)

        # 移動先に同名ファイルが存在する場合、タイムスタンプを付加
        if os.path.exists(dest_path):
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{name}_{timestamp}{ext}"
            dest_path = os.path.join(dest_dir, new_filename)
            logger.info(f"重複ファイル検出。新名で保存: {new_filename}")

        shutil.move(src_path, dest_path)
        logger.info(f"✓ 移動完了: {filename} → {dest_dir}")
        return True

    except PermissionError as e:
        logger.error(f"✗ 権限エラー: {filename} - {e}")
        return False
    except FileNotFoundError as e:
        logger.error(f"✗ ファイル不見つか: {filename} - {e}")
        return False
    except Exception as e:
        logger.error(f"✗ 予期しないエラー: {filename} - {e}")
        return False


# ==================== ファイルシステムイベントハンドラー ====================
class CleanerEventHandler(FileSystemEventHandler):
    """ファイル追加時に自動実行するハンドラー"""

    def on_created(self, event):
        """ファイルが作成されたときの処理"""
        if event.is_directory:
            return

        # 少し待機（ファイル書き込み完了を待つ）
        import time

        time.sleep(0.5)

        if is_valid_target_file(event.src_path):
            logger.info(f"🔍 対象ファイル検出: {os.path.basename(event.src_path)}")
            move_file_safely(event.src_path, DEST_DIR)


# ==================== メイン処理 ====================
def start_watcher():
    """ファイルシステム監視を開始"""
    if not os.path.exists(TARGET_DIR):
        logger.error(f"❌ 監視対象フォルダが見つかりません: {TARGET_DIR}")
        logger.error("clean_gemini.py の TARGET_DIR を確認してください")
        return False

    if not ensure_dest_dir_exists():
        return False

    logger.info("=" * 60)
    logger.info("🚀 お掃除エージェント起動")
    logger.info(f"   監視フォルダ: {TARGET_DIR}")
    logger.info(f"   移動先: {DEST_DIR}")
    logger.info(f"   対象拡張子: {', '.join(TRASH_EXTENSIONS)}")
    logger.info("=" * 60)

    observer = Observer()
    handler = CleanerEventHandler()
    observer.schedule(handler, TARGET_DIR, recursive=False)
    observer.start()

    try:
        while True:
            import time

            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("👋 お掃除エージェント停止（Ctrl+C）")
        observer.stop()
    finally:
        observer.join()
        logger.info("🛑 監視プロセス終了")


if __name__ == "__main__":
    start_watcher()
