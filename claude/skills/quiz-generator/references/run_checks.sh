#!/usr/bin/env bash
# 模試/問題集の「機械の関門」をまとめて通すランナー（2026-08-09 新設）。
#
# 使い方:
#   run_checks.sh <html> [log.json [range]]
#
# 動作:
#   1. (log.json を渡せば) カバレッジ検査 check_coverage.py
#   2. 答え漏れ検査 check_leak.py（見出しへの漏れがあれば終了コード非ゼロ＝ここで停止）
#   3. (log.json を渡せば) つまずき検査 check_pitfalls.py（関連/類似2-3のpitfall＋巻末▶）
#   どれかが失敗したら set -e により そこで止まる（次へ進めない＝ハード関門）。
#
# ★このランナーで強制できるのは「機械で判定できる関門」だけ。
#   ・配点/時間の検算（assert）は生成前に各自でPythonを流す（テスト固有のため）。
#   ・answer-validator（答えの中身の検証）は Claude のスキルでコードから起動できない。
#     → 最後に必ず起動することを掲示する（呼び忘れ防止）。
set -e
REF="$(cd "$(dirname "$0")" && pwd)"
PY="$(command -v python3 || command -v python)"
HTML="$1"; LOG="$2"; RANGE="$3"

if [ -z "$HTML" ]; then
  echo "使い方: run_checks.sh <html> [log.json [range]]"; exit 2
fi

if [ -n "$LOG" ]; then
  echo "▼ カバレッジ検査（材料が範囲を覆っているか）"
  if [ -n "$RANGE" ]; then
    "$PY" "$REF/check_coverage.py" "$LOG" --range "$RANGE"
  else
    "$PY" "$REF/check_coverage.py" "$LOG"
  fi
fi

echo "▼ 答え漏れ検査（見出しへの漏れは停止／設問文一致は注意）"
"$PY" "$REF/check_leak.py" "$HTML"

if [ -n "$LOG" ]; then
  echo "▼ つまずき検査（関連＝数学は類似2/3 に pitfall／巻末に ▶よくある誤り）"
  "$PY" "$REF/check_pitfalls.py" "$HTML" "$LOG"
fi

echo ""
echo "⛔ ここまでが機械の関門。次を必ず実施すること："
echo "   1) 配点・時間の検算（assert）を流したか"
echo "   2) answer-validator スキルを通したか（答えの中身の検証・省略禁止）"
