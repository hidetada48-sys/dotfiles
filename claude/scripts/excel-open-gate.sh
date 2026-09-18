#!/bin/bash
# エクセルを開く前の関門（PreToolUse / Bash）。判定の中身は excel-open-gate.py（同じフォルダ）。
# 体裁検査（tools/check_excel.py）の合格印が無いエクセルは開かせない（exit 2）。
# python が無い環境では黙って通す（Linux側でエクセルを開くことは稀なため）。
set -u
JUDGE="$(dirname "$0")/excel-open-gate.py"
[ -f "$JUDGE" ] || exit 0
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) ORDER="python py python3" ;;
  *)                    ORDER="python3 python" ;;
esac
PY=""
for c in $ORDER; do
  if command -v "$c" >/dev/null 2>&1 && [ "$("$c" -c 'print(1)' 2>/dev/null)" = "1" ]; then PY="$c"; break; fi
done
[ -z "$PY" ] && exit 0
if command -v cygpath >/dev/null 2>&1; then JUDGE="$(cygpath -w "$JUDGE")"; fi
PYTHONIOENCODING=utf-8 "$PY" "$JUDGE"
