#!/bin/bash
# claude関連ファイルをGoogle Driveにアップロードするスクリプト
# セッション終了時に自動実行される

GDRIVE_FOLDER="gdrive:claude-sync"
LOG_FILE="/tmp/claude-sync.log"

# rcloneをPATHから探し、見つからなければWinGet経由のパスを検索
if ! command -v rclone &>/dev/null; then
  RCLONE_PATH=$(find "$HOME/AppData/Local/Microsoft/WinGet/Packages" -name "rclone.exe" 2>/dev/null | head -1)
  [ -n "$RCLONE_PATH" ] && export PATH="$PATH:$(dirname "$RCLONE_PATH")"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] アップロード開始" >> "$LOG_FILE"

# メモリフォルダごとアップロード（MEMORY.md + 個別メモリファイル全て）
MEMORY_DIR=$(ls -d "$HOME/.claude/projects/"*/memory 2>/dev/null | head -1)
if [ -d "$MEMORY_DIR" ]; then
  rclone sync "$MEMORY_DIR" "$GDRIVE_FOLDER/memory/" 2>> "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] memoryフォルダをアップロードしました" >> "$LOG_FILE"
fi


# processed_ids.jsonをアップロード（ブックマーク処理済みリストをPC間で共有）
PROCESSED_IDS_FILE="$HOME/.x-bookmark-sync/processed_ids.json"
if [ -f "$PROCESSED_IDS_FILE" ]; then
  rclone copy "$PROCESSED_IDS_FILE" "$GDRIVE_FOLDER/" 2>> "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] processed_ids.jsonをアップロードしました" >> "$LOG_FILE"
fi

# basic-memory ノートをアップロード（セマンティック検索の元データ）
BASIC_MEMORY_DIR="$HOME/basic-memory"
if [ -d "$BASIC_MEMORY_DIR" ]; then
  rclone copy "$BASIC_MEMORY_DIR" "$GDRIVE_FOLDER/basic-memory/" 2>> "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] basic-memoryノートをアップロードしました" >> "$LOG_FILE"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] アップロード完了" >> "$LOG_FILE"
