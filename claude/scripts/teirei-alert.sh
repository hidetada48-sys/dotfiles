#!/bin/bash
# 定例業務の実施状況（SessionStart）＝起動時の通知を1本にまとめたもの（2026-10-04 専務承認）
# 役割：定例業務 24件（focus/定例業務/定例業務の台帳.csv）を判定し、月ごとの表を書き直して、要対応を Claude に知らせる。
#       これまでの12本（週初回・法改正・年次行事・有給・販売の月次・ジャンボ・在庫・生産日誌・日報・A重油・運賃・月次データ）を置き換える。
# 正典：docs/plans/2026-10-04-定例業務の通知の一覧（改修後）.md／CLAUDE.md 行動ルール0-10
# 判定は tools/teirei.py。python が無ければ「判定できません」と出す（黙らない）。

PROJECT="$HOME/mino-sakura-hq"
case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac
cd "$PROJECT" || exit 0
[ -f tools/teirei.py ] || exit 0

# 起動モードの案内（これまで週初回チェックが出していたもの）
echo ""
echo "【起動モード】専務モード(業務) / 裏方モード(仕組みづくり) / 休日モード。未宣言なら専務モードとみなす。"
echo "  ※裏方・休日モードなら、下の定例業務は実行しない（次の専務モード起動で実施）。"
echo "  ※【専務モードは毎回】当日の残作業一覧（focus/残作業一覧/残作業一覧_{今日}.md）を作り、チャットは下の定例業務の2行だけを出す（残作業一覧は表の1番から開く。CLAUDE.md 行動ルール0-3・0-10）。"

# Windows は python、Linux は python3（MS Store の偽物は弾く）
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) ORDER="python py python3" ;;
  *)                    ORDER="python3 python" ;;
esac
PY=""
for c in $ORDER; do
  if command -v "$c" >/dev/null 2>&1 && [ "$("$c" -c 'print(1)' 2>/dev/null)" = "1" ]; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo ""
  echo "========== 定例業務 =========="
  echo "  判定できませんでした（python がありません）。→ 【Claudeへ】専務に「定例業務を判定できませんでした」と1行で伝える。"
  echo "=============================="
  exit 0
fi

# 日報アプリの確定データ（社内サーバー）をリポジトリへコピーしてから判定する（届かなければ何もしない）
if [ -f production/scripts/nippo_server_pull.py ]; then
  PULL=$(PYTHONIOENCODING=utf-8 "$PY" production/scripts/nippo_server_pull.py 2>/dev/null)
  [ -n "$PULL" ] && { echo ""; echo "========== 日報の確定データ =========="; echo "$PULL"; }
fi

# .xls を読む部品（xlrd）が無ければ uv で足して流す
if "$PY" -c 'import xlrd, openpyxl' >/dev/null 2>&1; then
  PYTHONIOENCODING=utf-8 "$PY" tools/teirei.py 2>/dev/null
elif command -v uv >/dev/null 2>&1; then
  PYTHONIOENCODING=utf-8 uv run -q --with xlrd --with openpyxl --no-project python tools/teirei.py 2>/dev/null
else
  PYTHONIOENCODING=utf-8 "$PY" tools/teirei.py 2>/dev/null
fi
exit 0
