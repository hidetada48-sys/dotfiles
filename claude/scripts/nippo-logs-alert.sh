#!/bin/bash
# 日報の確定のあとアラート（SessionStart）：所感 → 現場記録の振り分け（2026-09-23 専務承認）＋抄き上げ重量表への書き込み（2026-09-28 追加）
# ＋サーバーの未読スキャン・確認待ちの日報（2026-10-04 追加）
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

# サーバーにまだ読み取っていない日報のスキャン・確認画面で確定していない日報（2026-10-04 専務指示「5（1）実施」）
# 日報アプリは専務が起動しないと動かないため、溜まっていても誰も知らせなかった。サーバーに届かない Linux では黙る
U=0; P=0
if [ -f production/scripts/nippo_unread_count.py ]; then
  UP=$("$PY" production/scripts/nippo_unread_count.py 2>/dev/null | tr -d '\r')
  U=$(echo "$UP" | awk '{print $2}'); P=$(echo "$UP" | awk '{print $4}')
  case "$U" in ''|*[!0-9]*) U=0 ;; esac
  case "$P" in ''|*[!0-9]*) P=0 ;; esac
fi

N=$("$PY" production/scripts/nippo_to_logs.py --count 2>/dev/null | tr -d '
')
case "$N" in ''|*[!0-9]*) N=0 ;; esac
# 抄き上げ重量表にまだ書いていない勤（2026-09-28：日報アプリの確定の中で書く作りをやめ、同じ耳打ちで Claude が書く）
W=0
if [ -f production/scripts/nippo_weight_sync.py ]; then
  W=$("$PY" production/scripts/nippo_weight_sync.py --count 2>/dev/null | tr -d '
')
  case "$W" in ''|*[!0-9]*) W=0 ;; esac
fi
[ "$N" -gt 0 ] || [ "$W" -gt 0 ] || [ -n "$PULL" ] || [ "$U" -gt 0 ] || [ "$P" -gt 0 ] || exit 0

echo ""
echo "========== 日報（未読スキャン ${U}本・確認待ち ${P}本／所感の振り分け ${N}欄／重量表に未書き込み ${W}勤） =========="
[ -n "$PULL" ] && echo "$PULL"
if [ "$U" -gt 0 ] || [ "$P" -gt 0 ]; then
echo "  ・サーバーに、日報アプリでまだ読み取っていない日報のスキャンが ${U}本、読み取ったが確定していない日報が ${P}本あります。"
echo "    → 【Claudeへ・専務モード】伺いの本筋で専務に伝える：日報アプリを開いて〔読み取り〕→確認画面で〔確定〕。"
echo "       確定するまで、所感の振り分けと抄き上げ重量表への書き込みは出てこない（読み取りは専務の操作。Claude は代わりに押さない）。"
fi
if [ "$N" -gt 0 ]; then
echo "  ・確定済みの日報に、まだ振り分けていない所感・停止ロスがあります。"
echo "    → 【Claudeへ・専務モード】伺わずに（専務指示 2026-09-30）nippo_to_logs.py で抜き出し、"
echo "       振り分けレポート（production/reports/日報振り分け_{今日}.md）を作ってリンクで提示する。"
echo "       採否は専務が決める（「上げない」の案は出さない）。手順は CLAUDE.md 行動ルール0-9。"
fi
if [ "$W" -gt 0 ]; then
echo "  ・確定済みの日報のうち ${W}勤が、抄き上げ重量表（サーバーの .xls）にまだ書かれていません。"
echo "    → 【Claudeへ】伺わずに書く（専務指示 2026-09-28＝b）：python production/scripts/nippo_weight_sync.py"
echo "       結果（書いた勤・書けなかった勤・人の値で書かなかった勤）を当日の残作業一覧のリード文に1行で残し、"
echo "       チャットでも必ず専務に報告する（専務指示 2026-09-30）。"
echo "       サーバーに届くのは Windows（専務PC）だけ。Linux の日は書かずに次の Windows 起動へ回す。"
fi
echo "=============================================================="
