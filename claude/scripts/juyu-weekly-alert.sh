#!/bin/bash
# A重油の週次単価（業者見積FAXの読み取り）アラート（SessionStart）
# 役割：見積は水〜木に届く。金曜以降の最初の起動で、今週（木曜はじまり）の見積が
#       CSVに入っていない業者があれば耳打ちする。入れば黙る（届かなかった業者も
#       単価空欄・備考「見積FAXなし」の1行で黙る）。
# 設計思想：事実通知のみ（サーバー取得はしない＝承認を得てから Claude が回す）。
#           判定は production/scripts/check_juyu_week.py。python が無ければ黙って終了。
# 正典：mino-sakura-hq CLAUDE.md 行動ルール 0-8／docs/plans/2026-09-18-A重油週次単価ルーティーン-design.md

PROJECT="$HOME/mino-sakura-hq"
case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac
cd "$PROJECT" || exit 0
[ -f production/scripts/check_juyu_week.py ] || exit 0

case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) ORDER="python py python3" ;;
  *)                    ORDER="python3 python" ;;
esac
PY=""
for c in $ORDER; do
  if command -v "$c" >/dev/null 2>&1 && [ "$("$c" -c 'print(1)' 2>/dev/null)" = "1" ]; then PY="$c"; break; fi
done
[ -z "$PY" ] && exit 0

RES=$(PYTHONIOENCODING=utf-8 "$PY" production/scripts/check_juyu_week.py 2>/dev/null)
[ -z "$RES" ] && exit 0
WEEK=$(printf '%s' "$RES" | cut -f1)
WHO=$(printf '%s' "$RES" | cut -f2)

echo ""
echo "========== A重油の週次単価（業者見積FAX） =========="
echo "  対象：${WEEK}（木）からの週／未読の業者：${WHO}"
echo "  → 専務の承認を得てからファイルサーバーのFAXを読むこと（無断取得は禁止）。"
echo "  手順：python production/scripts/juyu_fax_fetch.py     ← 取得・送り主の照合・単価表の切り出し"
echo "        切り出した画像を目で読み、production/data/A重油見積/業者別週次単価.csv に追記"
echo "        （届かなかった業者は単価空欄・備考『見積FAXなし』で1行）"
echo "        python production/scripts/juyu_weekly_report.py → python tools/check_excel.py <xlsx>"
echo "        → 画像を目で確かめ、8831のリンクで渡す。報告は1行（今週の最安・前週比・未着の業者）"
echo "  ※サーバーに届くのは Windows（専務PC）だけ。Linux起動日は進言まで。"
echo "=================================================="
echo ""
