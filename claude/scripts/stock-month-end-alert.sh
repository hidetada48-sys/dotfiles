#!/bin/bash
# 月末3倉庫 在庫集計アラート（SessionStart）
# 役割：暦月末で締まった先月分の在庫レポートが未作成なら耳打ちする。
#       専務の承認を得てから業務DBを読む（無断取得は禁止＝CLAUDE.md 大原則）。
# 設計思想：事実通知のみ（DB照会・スクリプト実行はしない＝フリーズ防止）。
#           python3非依存の純bash（Linux / Windows git-bash 共通）。
#           レポートが出来れば黙る。出来るまで出し続ける。

PROJECT="$HOME/mino-sakura-hq"

case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac

cd "$PROJECT" || exit 0

# --- 対象月＝先月（暦月）---
# ★ TZ=Asia/Tokyo は使わない（Windows git-bash に tzdata が無く黙って UTC に落ちるため）。
THIS_MONTH=$(date -u -d '+9 hours' +%Y-%m 2>/dev/null)
[ -n "$THIS_MONTH" ] || exit 0
TARGET=$(date -u -d "${THIS_MONTH}-01 -1 day" +%Y-%m 2>/dev/null)
[ -n "$TARGET" ] || exit 0

# 済み（レポートが在る）なら黙る
[ -f "production/reports/月末在庫_${TARGET}.md" ] && exit 0

echo ""
echo "========== 月末3倉庫 在庫集計 =========="
echo "  対象月：${TARGET}月末（暦月末）／レポート未作成"
echo "  出すもの：本社・美緑センター・アイカワの在庫を 商品ごと・倉庫ごと・3倉庫合計で。"
echo "            平判とそれ以外に分ける。数量（ケース）のみ。合計行は各表の先頭。"
echo ""
echo "  → 専務の承認を得てから業務DBを読むこと（無断取得は禁止）。"
echo "     毎月やるのは DBの商品マスタ と 区分表(production/data/在庫集計_商品区分.csv) の照合だけ。"
echo "     新商品が無ければ、集計対象・平判の区分は前月から不変。"
echo "     新商品が出たら集計対象かを専務に聞き、区分表へ追記する（通常／平判／除外）。"
echo ""
echo "  手順：python production/scripts/stock_month_end.py ${TARGET} --check   ← DBと区分表の照合だけ"
echo "        python production/scripts/stock_month_end.py ${TARGET}           ← レポート生成"
echo "        python tools/report_html.py --all → HTMLのURLだけを提示"
echo ""
echo "  ※商品台帳そのものが更新されたときだけ："
echo "        python production/scripts/build_stock_kubun.py --from-server"
echo "        （サーバーの台帳を取り込み区分表を作り直す。到達できるのは Windows=専務PC のみ）"
echo "======================================="
echo ""
