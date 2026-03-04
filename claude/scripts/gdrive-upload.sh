#!/bin/bash
# claude関連ファイルをGoogle Driveにアップロードするスクリプト
# セッション終了時に自動実行される

GDRIVE_FOLDER="gdrive:claude-sync"
LOG_FILE="/tmp/claude-sync.log"

# rcloneのパスを通す（インストール場所を自動検索）
RCLONE_PATH=$(find "$HOME/AppData/Local/Microsoft/WinGet/Packages" -name "rclone.exe" 2>/dev/null | head -1)
if [ -n "$RCLONE_PATH" ]; then
  export PATH="$PATH:$(dirname "$RCLONE_PATH")"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] アップロード開始" >> "$LOG_FILE"

# MEMORY.mdをアップロード（どのPCでも動的にパスを取得）
MEMORY_FILE=$(ls "$HOME/.claude/projects/"*/memory/MEMORY.md 2>/dev/null | head -1)
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
