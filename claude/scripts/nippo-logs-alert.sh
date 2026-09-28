#!/bin/bash
# 日報の確定のあとアラート（SessionStart）：所感 → 現場記録の振り分け（2026-09-23 専務承認）＋抄き上げ重量表への書き込み（2026-09-28 追加）
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

# 事務PCと専務PCの両方で日報アプリを動かす（2026-09-28 専務指示）：確定データはサーバーの共用フォルダに積まれるので、
# 数える前にリポジトリへ写す（順番は必ず「写す → 数える」。共用フォルダに届かない Linux などでは黙って何もしない）
PULL=""
if [ -f production/scripts/nippo_server_pull.py ]; then
  PULL=$("$PY" production/scripts/nippo_server_pull.py 2>/dev/null)
fi

N=$("$PY" production/scripts/nippo_to_logs.py --count 2>/dev/null | tr -d '')
case "$N" in ''|*[!0-9]*) N=0 ;; esac
# 抄き上げ重量表にまだ書いていない勤（2026-09-28：日報アプリの確定の中で書く作りをやめ、同じ耳打ちで Claude が書く）
W=0
if [ -f production/scripts/nippo_weight_sync.py ]; then
  W=$("$PY" production/scripts/nippo_weight_sync.py --count 2>/dev/null | tr -d '')
  case "$W" in ''|*[!0-9]*) W=0 ;; esac
fi
[ "$N" -gt 0 ] || [ "$W" -gt 0 ] || [ -n "$PULL" ] || exit 0

echo ""
echo "========== 日報の確定のあと（所感の振り分け ${N}欄／重量表に未書き込み ${W}勤） =========="
[ -n "$PULL" ] && echo "$PULL"
if [ "$N" -gt 0 ]; then
echo "  ・確定済みの日報に、まだ振り分けていない所感・停止ロスがあります。"
echo "    → 【Claudeへ・専務モード】まず「日報の未振り分けが ${N}欄あります。振り分けレポートを作りますか？」と聞き、承認を得てから"
echo "       nippo_to_logs.py で抜き出し、振り分けレポート（production/reports/日報振り分け_{今日}.md）を作る。"
echo "       採否は専務が決める（「上げない」の案は出さない）。手順は CLAUDE.md 行動ルール0-9。"
fi
if [ "$W" -gt 0 ]; then
echo "  ・確定済みの日報のうち ${W}勤が、抄き上げ重量表（サーバーの .xls）にまだ書かれていません。"
echo "    → 【Claudeへ】伺わずに書く（専務指示 2026-09-28＝b）：python production/scripts/nippo_weight_sync.py"
echo "       結果（書いた勤・書けなかった勤・人の値で書かなかった勤）を当日の残作業一覧のリード文に1行で残す。"
echo "       サーバーに届くのは Windows（専務PC）だけ。Linux の日は書かずに次の Windows 起動へ回す。"
fi
echo "=============================================================="
