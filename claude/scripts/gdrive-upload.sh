#!/bin/bash
# claude関連ファイルをGoogle Driveにアップロードする「起動係」
# 実際のアップロードは gdrive-upload-worker.sh が行う。ここは一瞬で終わる。
#
# 発火：PostToolUse（記憶を書いた直後）／Stop（ターン終了ごと・デバウンスあり）／SessionEnd／
#       SessionStart（前回の取りこぼし回収。gdrive-download.sh から --force で呼ばれる）
#
# ★2026-09-09 改修（Windowsの記憶がDriveに上がらない不具合）
#   原因: 本体をただの & で背景実行していたため、セッション終了と同時に道連れで殺され、
#         1分半かかるアップロードが最後まで走らなかった（SessionEnd発火では特に致命的）。
#   対策: setsid / nohup で親から完全に切り離し、セッションが消えても走り切らせる。
#         あわせて Stop（ターンごと）でも発火させ、セッションが生きている間に上げ切る。
#   使い方: gdrive-upload.sh [--force]   --force は待ち時間(デバウンス)を無視して必ず起動する

STAMP_FILE="/tmp/claude-gdrive-upload.stamp"   # 前回起動時刻（エポック秒）
FAIL_FLAG="/tmp/claude-gdrive-upload.failed"   # 前回に失敗が残っている印
DEBOUNCE_SEC=180                                # この秒数内の再アップロードはスキップ
WORKER="$(dirname "$0")/gdrive-upload-worker.sh"

FORCE=0
[ "$1" = "--force" ] && FORCE=1

# --- デバウンス：直近に起動済みならスキップ（前回失敗が残っていれば無視して必ず再試行） ---
NOW=$(date +%s 2>/dev/null)
if [ "$FORCE" -eq 0 ] && [ -n "$NOW" ] && [ -f "$STAMP_FILE" ] && [ ! -f "$FAIL_FLAG" ]; then
  LAST=$(cat "$STAMP_FILE" 2>/dev/null)
  case "$LAST" in
    ''|*[!0-9]*) LAST=0 ;;
  esac
  [ $((NOW - LAST)) -lt "$DEBOUNCE_SEC" ] && exit 0
fi
[ -n "$NOW" ] && printf '%s' "$NOW" > "$STAMP_FILE" 2>/dev/null

[ -f "$WORKER" ] || exit 0

# --- 本体を親から切り離して起動（セッションが終わっても走り切らせる） ---
if command -v setsid >/dev/null 2>&1; then
  setsid nohup bash "$WORKER" >/dev/null 2>&1 < /dev/null &
else
  # Windows(Git Bash)には setsid が無いので nohup のみ
  nohup bash "$WORKER" >/dev/null 2>&1 < /dev/null &
fi
disown 2>/dev/null

exit 0
