#!/bin/bash
# claude関連ファイルをGoogle Driveにアップロードするスクリプト
# セッション終了時に自動実行される

GDRIVE_FOLDER="gdrive:claude-sync"
LOG_FILE="/tmp/claude-sync.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] アップロード開始" >> "$LOG_FILE"

# MEMORY.mdをアップロード
MEMORY_FILE="$HOME/.claude/projects/-home-hidetada48/memory/MEMORY.md"
if [ -f "$MEMORY_FILE" ]; then
  rclone copy "$MEMORY_FILE" "$GDRIVE_FOLDER/" 2>> "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] MEMORY.mdをアップロードしました" >> "$LOG_FILE"
fi

# claude-mem DBをアップロード
DB_FILE="$HOME/.claude-mem/claude-mem.db"
if [ -f "$DB_FILE" ]; then
  rclone copy "$DB_FILE" "$GDRIVE_FOLDER/" 2>> "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] DBをアップロードしました" >> "$LOG_FILE"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] アップロード完了" >> "$LOG_FILE"
