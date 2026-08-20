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
#   4. (模試のみ) 承認ターン検査 check_approvals.py（質問/承認ターンを飛ばしていないか）
#   どれかが失敗したら set -e により そこで止まる（次へ進めない＝ハード関門）。
#
# ★このランナーで強制できるのは「機械で判定できる関門」だけ。
#   ・配点/時間の検算（assert）は生成前に各自でPythonを流す（テスト固有のため）。
#   ・answer-validator（答えの中身の検証）は Claude のスキルでコードから起動できない。
#     → 最後に必ず起動することを掲示する（呼び忘れ防止）。
set -e
REF="$(cd "$(dirname "$0")" && pwd)"
# Python の選び方（2026-08-17）：Windows では `python3` が Microsoft Store のダミーに
# 当たり、「Python」と表示して終了コード49で落ちる。存在するだけでは判定できないので、
# 実際に走るかどうかで選ぶ。
pick_py(){
  for c in python3 python py; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys" >/dev/null 2>&1; then
      echo "$c"; return 0
    fi
  done
  return 1
}
PY="$(pick_py)" || { echo "[NG] 実行できる python が見つからない"; exit 2; }
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

# 配点・時間の検算（模試の出題履歴JSONに daimon_summary があるときだけ・2026-08-13 機械化）。
# 旧来は「各自でassertを流す」honor systemだったが飛ばされたので run_checks に取り込む。
if [ -n "$LOG" ]; then
  echo "▼ 配点・時間の検算（模試のみ・questions[].point 合計 == total_points）"
  "$PY" - "$LOG" <<'PY'
import sys, json
d = json.load(open(sys.argv[1], encoding="utf-8"))
# 模試=questions / 類題集=problems で判定（2026-08-18 修正：旧版は daimon_summary 判定で、
# スキルが daimon_summary を出さないため全模試が skip し配点検算が無効化していた）。
qs = d.get("questions")
if qs is None:
    print("  [skip] questions 無し＝類題集 or 検算対象外"); sys.exit(0)
declared = d.get("declared_total_points", d.get("total_points"))
ds = d.get("daimon_summary")
if ds:
    pts = sum(x.get("points", 0) for x in ds); src = "daimon_summary"
else:
    pts = sum(x.get("point", 0) for x in qs); src = "questions[].point"
if declared is None:
    print("  [NG] 満点が宣言されていない（total_points / declared_total_points が無い）"); sys.exit(1)
if pts == 0:
    print("  [NG] 配点が読めない（daimon_summary も questions[].point も無い）"
          "＝模試の出題履歴JSONに各設問の point か daimon_summary を持たせること"); sys.exit(1)
ok = True
if pts != declared:
    print(f"  [NG] 配点合計 {pts} ≠ 宣言 {declared}（{src}）"); ok = False
else:
    print(f"  [OK] 配点合計 {pts} = 宣言 {declared}（{src}）")
tl = d.get("time_minutes", d.get("time_limit"))
if ds and tl is not None and all("time_minutes" in x for x in ds):
    tt = sum(x["time_minutes"] for x in ds)
    if tt != tl:
        print(f"  [NG] 目安時間合計 {tt} ≠ 宣言 {tl}"); ok = False
    else:
        print(f"  [OK] 目安時間合計 {tt} = 宣言 {tl}")
sys.exit(0 if ok else 1)
PY
fi

if [ -n "$LOG" ]; then
  echo "▼ 承認ターンの検査（模試のみ・質問/承認を飛ばしていないか）"
  "$PY" "$REF/check_approvals.py" "$LOG"
fi

# 難易度構成の検査（模試のみ・2026-08-19 新設／2026-08-20 2軸化）。
# 配点移動だけで「応用」を名乗る抜け穴を塞ぐ。difficulty_primary で主軸を切替え、
# complexity(数学等)は内容の複雑さ(low/mid/high)、process(暗記系)は load(recall/select/construct)
# の設問数構成比が level(基本/標準/応用) の基準を満たさなければ set -e で停止する。
if [ -n "$LOG" ]; then
  echo "▼ 難易度構成の検査（模試のみ・2軸：complexity=数学等／process=暗記系）"
  "$PY" "$REF/check_difficulty.py" "$LOG"
fi

echo ""
echo "⛔ ここまでが機械の関門（漏れ・つまずき・配点）。残る必須は answer-validator："
echo "   answer-validator スキルを通し、最後に av_stamp.py で合格スタンプを発行すること。"
echo "   （publish_to_drive.sh は sha256一致の合格スタンプが無いと配信を拒否する）"
