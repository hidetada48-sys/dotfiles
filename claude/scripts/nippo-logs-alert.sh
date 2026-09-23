#!/bin/bash
# 日報の所感 → 現場記録 の振り分けアラート（SessionStart・2026-09-23 専務承認）
# 役割：確定済みの日報に、まだ振り分けていない所感・停止ロスがあれば件数を耳打ちする。
# 設計：docs/plans/2026-09-23-日報の所感を現場記録へ-design.md
# 事実通知のみ（書き込みはしない）。python が無い環境では黙って終える。出来れば黙る。

PROJECT="$HOME/mino-sakura-hq"

case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac

cd "$PROJECT" || exit 0
[ -f production/scripts/nippo_to_logs.py ] || exit 0

# Windows は python、Linux は python3
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys" >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -n "$PY" ] || exit 0

N=$("$PY" production/scripts/nippo_to_logs.py --count 2>/dev/null | tr -d '\r')
case "$N" in ''|*[!0-9]*) exit 0 ;; esac
[ "$N" -gt 0 ] || exit 0

echo ""
echo "========== 日報の所感 → 現場記録（未振り分け ${N}欄） =========="
echo "  確定済みの日報に、まだ振り分けていない所感・停止ロスがあります。"
echo "  → 【Claudeへ・専務モード】まず「日報の未振り分けが ${N}欄あります。振り分けレポートを作りますか？」と聞き、承認を得てから"
echo "     nippo_to_logs.py で抜き出し、振り分けレポート（production/reports/日報振り分け_{今日}.md）を作る。"
echo "     採否は専務が決める（「上げない」の案は出さない）。手順は CLAUDE.md 行動ルール0-9。"
echo "=============================================================="
