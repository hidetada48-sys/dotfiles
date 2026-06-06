#!/bin/bash
# claude関連ファイルをGoogle Driveにアップロードするスクリプト
# SessionEndフック（セッション終了時）と basic-memory 保存後（PostToolUse）に発火する。
# ※2026-06-07: 発火タイミングを Stop（毎ターン）→ SessionEnd（終了時）に変更。
#   gdrive同期は Windows との記憶共有が目的で、毎ターン走らせる必要はないため
#   「記憶を書いたとき（PostToolUse）＋セッションの区切り（SessionEnd）」だけに絞った。
#
# フリーズ対策（2026-06-06 改修）：
#   旧版は rclone をその場でブロック実行し、毎ターン約38秒固まっていた。
#   - デバウンス: 前回アップロードから一定時間内なら即スキップ（連続実行させない）
#   - バックグラウンド実行: アップロード本体を裏に回しターンを一切ブロックしない
#   - 二重起動防止ロック: 前回のアップロードが走行中なら新規起動しない
#   - rclone にタイムアウト/高速化フラグを付与（裏の処理も暴走・ハングさせない）
#   - 何があってもセッションは止めない（常に exit 0）
#   - Windows(Git Bash)/Linux 両対応

GDRIVE_FOLDER="gdrive:claude-sync"
LOG_FILE="/tmp/claude-sync.log"
STAMP_FILE="/tmp/claude-gdrive-upload.stamp"   # 前回アップロード時刻（エポック秒）
LOCK_DIR="/tmp/claude-gdrive-upload.lock"      # 二重起動防止ロック
DEBOUNCE_SEC=180                                # この秒数内の再アップロードはスキップ

# --- デバウンス: 直近にアップロード済みなら即終了（ターンをブロックしない） ---
NOW=$(date +%s 2>/dev/null)
if [ -n "$NOW" ] && [ -f "$STAMP_FILE" ]; then
  LAST=$(cat "$STAMP_FILE" 2>/dev/null)
  case "$LAST" in
    ''|*[!0-9]*) LAST=0 ;;   # 数値でなければ0扱い
  esac
  if [ $((NOW - LAST)) -lt "$DEBOUNCE_SEC" ]; then
    exit 0
  fi
fi

# 今回の時刻を記録（成否に関わらずデバウンス基準を更新する）
[ -n "$NOW" ] && printf '%s' "$NOW" > "$STAMP_FILE" 2>/dev/null

# --- 実アップロードはバックグラウンドで実行（ターンを止めない） ---
(
  # 二重起動防止: ロックが取れなければ何もしない（前回処理がまだ走行中）
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    exit 0
  fi
  trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT  # 終了時に必ずロック解除

  # rclone を PATH から探し、無ければ WinGet 経由のパスを検索
  if ! command -v rclone >/dev/null 2>&1; then
    RCLONE_PATH=$(find "$HOME/AppData/Local/Microsoft/WinGet/Packages" -name "rclone.exe" 2>/dev/null | head -1)
    [ -n "$RCLONE_PATH" ] && export PATH="$PATH:$(dirname "$RCLONE_PATH")"
  fi
  # rclone が無ければ静かに終了（未インストール環境ではスキップ）
  command -v rclone >/dev/null 2>&1 || exit 0

  # ハング防止＆高速化フラグ（接続10秒・通信30秒で打ち切り、並列・リトライ最小）
  RFLAGS="--contimeout=10s --timeout=30s --retries=1 --low-level-retries=2 --transfers=8 --checkers=8"

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] アップロード開始(背景)" >> "$LOG_FILE"

  # メモリフォルダごとアップロード（MEMORY.md + 個別メモリファイル全て）
  MEMORY_DIR=$(ls -d "$HOME/.claude/projects/"*/memory 2>/dev/null | head -1)
  if [ -d "$MEMORY_DIR" ]; then
    rclone sync $RFLAGS "$MEMORY_DIR" "$GDRIVE_FOLDER/memory/" 2>> "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] memoryフォルダをアップロードしました" >> "$LOG_FILE"
  fi

  # processed_ids.json をアップロード（ブックマーク処理済みリストをPC間で共有）
  PROCESSED_IDS_FILE="$HOME/.x-bookmark-sync/processed_ids.json"
  if [ -f "$PROCESSED_IDS_FILE" ]; then
    rclone copy $RFLAGS "$PROCESSED_IDS_FILE" "$GDRIVE_FOLDER/" 2>> "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] processed_ids.jsonをアップロードしました" >> "$LOG_FILE"
  fi

  # basic-memory ノートをアップロード（セマンティック検索の元データ）
  BASIC_MEMORY_DIR="$HOME/basic-memory"
  if [ -d "$BASIC_MEMORY_DIR" ]; then
    rclone copy $RFLAGS "$BASIC_MEMORY_DIR" "$GDRIVE_FOLDER/basic-memory/" 2>> "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] basic-memoryノートをアップロードしました" >> "$LOG_FILE"
  fi

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] アップロード完了(背景)" >> "$LOG_FILE"
) >/dev/null 2>&1 &

# バックグラウンドジョブを親から切り離してフックを即終了（セッションを止めない）
disown 2>/dev/null

exit 0
