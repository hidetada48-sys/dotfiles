#!/bin/bash
# 運送会社の運賃計算アラート（SessionStart）
# 役割：月が替わったら、前月分の運賃計算表（請求書の検算用）が未作成なら耳打ちする。
#       専務の承認を得てから業務DBを読む（無断取得は禁止＝CLAUDE.md 大原則）。
# 設計思想：事実通知のみ（DB照会・スクリプト実行はしない＝フリーズ防止）。
#           python3非依存の純bash（Linux / Windows git-bash 共通）。
#           計算表が出来れば黙る。出来るまで出し続ける。
# 設計：docs/plans/2026-09-11-運送会社運賃計算ルーティーン-design.md

PROJECT="$HOME/mino-sakura-hq"

case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac

cd "$PROJECT" || exit 0

# --- 対象月＝前月（＝請求の月）---
# ★ TZ=Asia/Tokyo は使わない（Windows git-bash に tzdata が無く黙って UTC に落ちるため）。
THIS_MONTH=$(date -u -d '+9 hours' +%Y-%m 2>/dev/null)
[ -n "$THIS_MONTH" ] || exit 0
TARGET=$(date -u -d "${THIS_MONTH}-01 -1 day" +%Y-%m 2>/dev/null)
[ -n "$TARGET" ] || exit 0

# 済み（計算表が在る）なら黙る
[ -f "finance/reports/運賃計算/運賃計算_${TARGET}.html" ] && exit 0

# アイカワの期間＝前々月21日〜前月20日／櫻井＝前月1日〜末日
PREV=$(date -u -d "${TARGET}-01 -1 day" +%Y-%m 2>/dev/null)
A_FROM="${PREV}-21"
A_TO="${TARGET}-20"
S_FROM="${TARGET}-01"
S_TO=$(date -u -d "${THIS_MONTH}-01 -1 day" +%Y-%m-%d 2>/dev/null)

# 原料日誌が対象月まで取り込めているか（未取込なら原料運賃が欠ける）
GENRYO_NOTE=""
if ls production/inbox/原料/*.pdf >/dev/null 2>&1; then
  GENRYO_NOTE="  ⚠️ 原料日誌に未取込のPDFがあります。先に取り込むこと（原料運賃が欠けます）。"
fi

echo ""
echo "========== 運送会社の運賃計算（請求書の検算） =========="
echo "  対象月：${TARGET}分／計算表 未作成"
echo "    アイカワ運輸：積込日 ${A_FROM} 〜 ${A_TO}"
echo "    櫻井商事　　：積込日 ${S_FROM} 〜 ${S_TO}"
echo ""
echo "  → 専務の承認を得てから業務DBを読むこと（無断取得は禁止）。"
echo "     承認の前に聞くこと：前月末までの積込分の売上伝票は入力済みか（未入力なら待つ）。"
[ -n "$GENRYO_NOTE" ] && echo "$GENRYO_NOTE"
echo ""
echo "  手順：python finance/scripts/freight_calc.py ${TARGET}"
echo "        python tools/report_html.py --all → HTMLのURLだけを提示"
echo "        確認欄に出た便があれば、その件数を1行添える"
echo "======================================================="
echo ""
