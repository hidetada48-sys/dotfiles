#!/bin/bash
# レポート目次フル更新（SessionStart）
# 役割：美濃桜HQで起動するたび、現存する全レポートを目次(.reports_html/index.html)へ反映する。
#       report_html.py --all を機械的に1回流すだけ（md非経由の単体HTML成果物もこぼさない＝専務指示 2026-07-06）。
# 設計思想：静かに実行（耳打ちしない・純粋な保守処理）。python/markdown が無ければ黙ってスキップ。
#           出力は捨てる。失敗しても常に exit 0（起動を止めない）。両OS（Linux / Windows git-bash）共通。

PROJECT="$HOME/mino-sakura-hq"

# このプロジェクト内で起動したときだけ動く（他リポジトリ・素の場所では何もしない）
case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac

TOOL="$PROJECT/tools/report_html.py"
[ -f "$TOOL" ] || exit 0

# --- python + markdown ライブラリが揃っているものを選ぶ（無ければスキップ）---
# Windows(git-bash)は python、Linuxは python3 を優先。import markdown が通るものだけ採用する。
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) ORDER="python python3" ;;
  *)                    ORDER="python3 python" ;;
esac

PY=""
for c in $ORDER; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import markdown" >/dev/null 2>&1; then
    PY="$c"; break
  fi
done
[ -n "$PY" ] || exit 0

# --- 目次をフル更新（出力は捨てる・失敗しても起動は止めない）---
# report_html.py 内で REPO を __file__ から解決するため、cd 不要でパス非依存に動く。
"$PY" "$TOOL" --all >/dev/null 2>&1

exit 0
