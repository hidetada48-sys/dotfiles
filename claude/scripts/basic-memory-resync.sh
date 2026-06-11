#!/bin/bash
# basic-memory のDB同期ズレを自動修復する（記憶共有システムの安定化）
#
# 背景:
#   gdrive-download 後にノートファイルの mtime が変わることがある。
#   MCP の watch がその変化を拾えていないと、DB と実ファイルがズレ、
#   最新の記憶が検索に出てこなくなる（手動 reindex するまで直らない）。
#   これをセッション開始時に自動で検出し、ズレていれば reindex で直す。
#
# フリーズ防止（最優先ルール）:
#   basic-memory CLI の起動も reindex も数秒かかるため、全処理を
#   バックグラウンドに回し、セッション開始を一切ブロックしない。
#
# マルチ環境対応:
#   basic-memory が無い環境（Windows機など未導入時）は静かにスキップする。

LOG_FILE="/tmp/basic-memory-resync.log"

# basic-memory コマンドを解決（直接インストール > uvx の順）。無ければ空文字。
resolve_bm() {
  if command -v basic-memory >/dev/null 2>&1; then
    echo "basic-memory"
  elif command -v uvx >/dev/null 2>&1; then
    echo "uvx basic-memory"
  else
    echo ""
  fi
}

# 実処理はすべてバックグラウンドで実行し、セッション開始を止めない
(
  BM=$(resolve_bm)
  [ -z "$BM" ] && exit 0   # 未導入環境（Windows等）はスキップ

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] resync判定開始" >> "$LOG_FILE"

  # 同期状態を取得（出力に "No changes" があればズレ無し）
  STATUS=$($BM status 2>/dev/null)
  if printf '%s' "$STATUS" | grep -q "No changes"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ズレなし。reindex不要" >> "$LOG_FILE"
    exit 0
  fi

  # ズレ検出 → 差分だけ取り込む（incremental reindex は変更分のみで軽い）
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 同期ズレ検出 → reindex実行" >> "$LOG_FILE"
  $BM reindex --project main >> "$LOG_FILE" 2>&1
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] reindex完了" >> "$LOG_FILE"
) >/dev/null 2>&1 &

# バックグラウンドジョブを親から切り離してフックを即終了（セッションを止めない）
disown 2>/dev/null
exit 0
