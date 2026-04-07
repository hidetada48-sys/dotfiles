#!/bin/bash
# Google Driveからclaude関連ファイルをダウンロードするスクリプト
# セッション開始時に自動実行される

GDRIVE_FOLDER="gdrive:claude-sync"
LOG_FILE="/tmp/claude-sync.log"

# rcloneをPATHから探し、見つからなければWinGet経由のパスを検索
if ! command -v rclone &>/dev/null; then
  RCLONE_PATH=$(find "$HOME/AppData/Local/Microsoft/WinGet/Packages" -name "rclone.exe" 2>/dev/null | head -1)
  [ -n "$RCLONE_PATH" ] && export PATH="$PATH:$(dirname "$RCLONE_PATH")"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ダウンロード開始" >> "$LOG_FILE"

# MEMORY.mdをダウンロード（projectsディレクトリから動的にパスを取得）
MEMORY_DIR=$(ls -d "$HOME/.claude/projects/"*/memory 2>/dev/null | head -1)
if [ -z "$MEMORY_DIR" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] memoryディレクトリが見つかりません" >> "$LOG_FILE"
  exit 1
fi
rclone sync "$GDRIVE_FOLDER/memory/" "$MEMORY_DIR/" 2>> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] memoryフォルダをダウンロードしました" >> "$LOG_FILE"


# processed_ids.jsonをダウンロード（ブックマーク処理済みリストをPC間で共有）
BOOKMARK_SYNC_DIR="$HOME/.x-bookmark-sync"
mkdir -p "$BOOKMARK_SYNC_DIR"
rclone copy "$GDRIVE_FOLDER/processed_ids.json" "$BOOKMARK_SYNC_DIR/" --update 2>> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] processed_ids.jsonをダウンロードしました" >> "$LOG_FILE"

# basic-memory ノートをダウンロード（セマンティック検索の元データ）
BASIC_MEMORY_DIR="$HOME/basic-memory"
mkdir -p "$BASIC_MEMORY_DIR"
rclone sync "$GDRIVE_FOLDER/basic-memory/" "$BASIC_MEMORY_DIR" 2>> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] basic-memoryノートをダウンロードしました" >> "$LOG_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ダウンロード完了" >> "$LOG_FILE"
