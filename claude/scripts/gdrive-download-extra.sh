#!/bin/bash
# Google Driveからの「急がないダウンロード」（gdrive-download.sh が裏で起動する）
# 記憶（auto-memory / basic-memory）はセッション開始前に要るので本体側で取るが、
# 業務データの仮置場や機密ファイルは開始直後に無くても困らない。
# ここに回すことでセッション開始の待ち時間を短くしている。

source "$(dirname "$0")/gdrive-sync-lib.sh"

GDRIVE_FOLDER="gdrive:claude-sync"
LOG_FILE="/tmp/claude-sync.log"
LOCK_DIR="/tmp/claude-gdrive-download-extra.lock"

# 二重起動防止（10分以上古いロックは死骸として奪う）
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  AGE=$(( $(date +%s) - $(stat -c %Y "$LOCK_DIR" 2>/dev/null || echo 0) ))
  [ "$AGE" -gt 600 ] || exit 0
  rmdir "$LOCK_DIR" 2>/dev/null; mkdir "$LOCK_DIR" 2>/dev/null || exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT

gs_find_rclone || exit 0
RFLAGS="--contimeout=15s --timeout=120s --retries=3 --low-level-retries=10 --transfers=4 --checkers=4 --fast-list"

# ブックマーク処理済みリスト（PC間で共有）
mkdir -p "$HOME/.x-bookmark-sync"
rclone copy $RFLAGS --update "$GDRIVE_FOLDER/processed_ids.json" "$HOME/.x-bookmark-sync/" 2>> "$LOG_FILE"

SALES_PROJECT="$HOME/mino-sakura-hq"
if [ -d "$SALES_PROJECT" ]; then
  # 生産データは原本へ直接落とさず inbox で受ける
  # （2026-07-10 に単価表が原料日誌807行を丸ごと上書きした事故があったため）
  mkdir -p "$SALES_PROJECT/production/inbox"
  rclone copy $RFLAGS --update "$GDRIVE_FOLDER/production-inbox/" "$SALES_PROJECT/production/inbox/" 2>> "$LOG_FILE"

  # 機密ファイル（社員台帳・有給付与一覧など）
  mkdir -p "$SALES_PROJECT/secrets/hr"
  rclone copy $RFLAGS --update "$GDRIVE_FOLDER/secrets-hr/" "$SALES_PROJECT/secrets/hr/" 2>> "$LOG_FILE"

  # 回答のレポート（もう一方のPCで作った答え）。2026-10-13 専務叱責で2台にそろえる
  mkdir -p "$SALES_PROJECT/private/answers"
  rclone copy $RFLAGS --update --include "*.md" "$GDRIVE_FOLDER/private-answers/" "$SALES_PROJECT/private/answers/" 2>> "$LOG_FILE"
  # 届いた答えのうち HTML が無い物だけ HTML にする（リンクで開けるように）
  PY=python3; command -v python3 >/dev/null 2>&1 && python3 -c "" 2>/dev/null || PY=python
  NEW=()
  for f in "$SALES_PROJECT"/private/answers/*.md; do
    [ -e "$f" ] || continue
    b=$(basename "$f" .md)
    [ -f "$SALES_PROJECT/.reports_html/private/answers/$b.html" ] || NEW+=("private/answers/$b.md")
  done
  if [ ${#NEW[@]} -gt 0 ] && command -v "$PY" >/dev/null 2>&1; then
    (cd "$SALES_PROJECT" && "$PY" tools/report_html.py "${NEW[@]}" >> "$LOG_FILE" 2>&1)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 回答のレポート ${#NEW[@]}本を HTML にしました" >> "$LOG_FILE"
  fi
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 業務データのダウンロード完了(背景)" >> "$LOG_FILE"
exit 0
