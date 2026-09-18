#!/bin/bash
# レポート配信サーバー（127.0.0.1:8830）を、落ちていたら起こす。
# 役割：HTML鉄則で提示するURL http://127.0.0.1:8830/… を常に開ける状態に保つ。
# 設計：静かに実行・失敗しても exit 0（起動を止めない）。Linux / Windows(git-bash) 共通。
#       ループバック限定（社外非公開）。既に上がっていれば何もしない。
# 配線：settings.json の SessionStart に  bash ~/.claude/scripts/report-serve.sh

set -u
PORT=8830
REPO="$HOME/mino-sakura-hq"
OUT="$REPO/.reports_html"

[ -d "$REPO" ] || exit 0

# すでに listen していれば起こさない（エクセルの受付 8831 は下で別に見る）
UP8830=0
if command -v curl >/dev/null 2>&1; then
    curl -s -m 2 -o /dev/null "http://127.0.0.1:$PORT/" && UP8830=1
fi

mkdir -p "$OUT" 2>/dev/null

# 実際に動く python を選ぶ（Windowsの python3 はStoreのダミーで無反応）
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) ORDER="python py python3" ;;
  *)                    ORDER="python3 python" ;;
esac
PY=""
for c in $ORDER; do
    if command -v "$c" >/dev/null 2>&1 && [ "$("$c" -c 'print(1)' 2>/dev/null)" = "1" ]; then
        PY="$c"; break
    fi
done
[ -z "$PY" ] && exit 0

DIR_ARG="$OUT"
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*)
    command -v cygpath >/dev/null 2>&1 && DIR_ARG="$(cygpath -w "$OUT")" ;;
esac

if [ "$UP8830" = "0" ]; then
    nohup "$PY" -m http.server "$PORT" --bind 127.0.0.1 --directory "$DIR_ARG" \
          >/dev/null 2>&1 &
    disown 2>/dev/null
fi

# エクセルの受付（127.0.0.1:8831）＝チャットのリンクからエクセルを開く（2026-09-18 専務指示）
# 正体：$REPO/tools/xlsx_opener.py。落ちていたら起こす。
OPENER="$REPO/tools/xlsx_opener.py"
if [ -f "$OPENER" ]; then
    UP8831=0
    command -v curl >/dev/null 2>&1 && curl -s -m 2 -o /dev/null "http://127.0.0.1:8831/" && UP8831=1
    if [ "$UP8831" = "0" ]; then
        OP_ARG="$OPENER"
        command -v cygpath >/dev/null 2>&1 && OP_ARG="$(cygpath -w "$OPENER")"
        nohup "$PY" "$OP_ARG" >/dev/null 2>&1 &
        disown 2>/dev/null
    fi
fi
exit 0
