#!/bin/bash
# Google Driveからclaude関連ファイルをダウンロードするスクリプト
# セッション開始時に自動実行される

GDRIVE_FOLDER="gdrive:claude-sync"
LOG_FILE="/tmp/claude-sync.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ダウンロード開始" >> "$LOG_FILE"

# MEMORY.mdをダウンロード
MEMORY_DIR="$HOME/.claude/projects/-home-hidetada48/memory"
mkdir -p "$MEMORY_DIR"
rclone copy "$GDRIVE_FOLDER/MEMORY.md" "$MEMORY_DIR/" --update 2>> "$LOG_FILE"

# claude-mem DBをダウンロード（ファイルが存在しない場合のみ）
DB_DIR="$HOME/.claude-mem"
mkdir -p "$DB_DIR"
if [ ! -f "$DB_DIR/claude-mem.db" ]; then
  rclone copy "$GDRIVE_FOLDER/claude-mem.db" "$DB_DIR/" 2>> "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] DBをダウンロードしました" >> "$LOG_FILE"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ダウンロード完了" >> "$LOG_FILE"
