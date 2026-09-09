#!/bin/bash
# Google Driveへのアップロード本体（gdrive-upload.sh から切り離して実行される）
# ここは時間のかかる処理。呼び出し元とは親子関係を切って動くので、
# セッションが終了しても最後まで走り切る（従来はここで殺されて記憶が届かなかった）。

source "$(dirname "$0")/gdrive-sync-lib.sh"

GDRIVE_FOLDER="gdrive:claude-sync"
LOG_FILE="/tmp/claude-sync.log"
LOCK_DIR="/tmp/claude-gdrive-upload.lock"
FAIL_FLAG="/tmp/claude-gdrive-upload.failed"
LOCK_STALE_SEC=900

# --- 二重起動防止（前回がまだ走っていれば何もしない） ---
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "$LOCK_DIR" 2>/dev/null || echo 0) ))
  if [ "$LOCK_AGE" -gt "$LOCK_STALE_SEC" ]; then
    rmdir "$LOCK_DIR" 2>/dev/null
    mkdir "$LOCK_DIR" 2>/dev/null || exit 0
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 古いロックを解除して再開しました" >> "$LOG_FILE"
  else
    exit 0
  fi
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT

# rclone が無い環境では、黙って消えずに「同期していない」ことを記録して終わる
if ! gs_find_rclone; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ★rclone未導入のため同期していません" >> "$LOG_FILE"
  touch "$FAIL_FLAG" 2>/dev/null
  exit 0
fi

# API制限(403)対策とハング防止のフラグ
RFLAGS="--contimeout=15s --timeout=120s --retries=3 --low-level-retries=10 --transfers=4 --checkers=4 --fast-list --drive-pacer-min-sleep=100ms --drive-pacer-burst=20"

UPLOAD_NG=0

# rclone を実行し、成否を正直にログへ記録する（失敗を成功と書かない）
run_rclone() {
  local label="$1"; shift
  rclone "$@" 2>> "$LOG_FILE"
  local rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${label}をアップロードしました" >> "$LOG_FILE"
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ★失敗: ${label} のアップロードに失敗しました (rclone rc=$rc)" >> "$LOG_FILE"
    touch "$FAIL_FLAG" 2>/dev/null
    UPLOAD_NG=1
  fi
}

rm -f "$FAIL_FLAG" 2>/dev/null
echo "[$(date '+%Y-%m-%d %H:%M:%S')] アップロード開始(背景)" >> "$LOG_FILE"

# --- ① auto-memory：全プロジェクトのmemoryを、PC共通のキー別フォルダへ ---
# いったんローカルの仮置場に「キー別」で並べ替えてから、rclone 1回でまとめて送る。
# （プロジェクトごとに rclone を呼ぶと1個あたり約1分かかり、6個で4分かかっていた）
# ※sync(ミラー)は使わない。片方のPCに無いファイルをDriveから消してしまうため。
STAGE_UP="/tmp/claude-memory-upload"
rm -rf "$STAGE_UP" 2>/dev/null
for MEMDIR in "$HOME/.claude/projects/"*/memory; do
  [ -d "$MEMDIR" ] || continue
  ls "$MEMDIR"/*.md >/dev/null 2>&1 || continue   # 空フォルダはスキップ
  KEY=$(gs_canon "$(basename "$(dirname "$MEMDIR")")")
  mkdir -p "$STAGE_UP/$KEY"
  cp -p "$MEMDIR"/*.md "$STAGE_UP/$KEY/" 2>/dev/null   # -p で更新日時を保つ（--update の判定に必要）
done
if [ -d "$STAGE_UP" ]; then
  run_rclone "memory(全プロジェクト)" copy $RFLAGS --update "$STAGE_UP" "$GDRIVE_FOLDER/memory-by-project/"
  rm -rf "$STAGE_UP" 2>/dev/null
fi

# --- ② basic-memory ノート（セマンティック検索の元データ） ---
[ -d "$HOME/basic-memory" ] && \
  run_rclone "basic-memoryノート" copy $RFLAGS --update "$HOME/basic-memory" "$GDRIVE_FOLDER/basic-memory/"

# --- ③ ブックマーク処理済みリスト ---
[ -f "$HOME/.x-bookmark-sync/processed_ids.json" ] && \
  run_rclone "processed_ids.json" copy $RFLAGS "$HOME/.x-bookmark-sync/processed_ids.json" "$GDRIVE_FOLDER/"

# --- ④ 機密ファイル（社員台帳・有給付与一覧など） ---
[ -d "$HOME/mino-sakura-hq/secrets/hr" ] && \
  run_rclone "secrets/hr（機密）" copy $RFLAGS --update "$HOME/mino-sakura-hq/secrets/hr/" "$GDRIVE_FOLDER/secrets-hr/"

if [ "$UPLOAD_NG" -eq 0 ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] アップロード完了(背景) 全て成功" >> "$LOG_FILE"
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ★アップロード完了(背景) 失敗あり。次回セッション開始時に再試行します" >> "$LOG_FILE"
fi
exit 0
