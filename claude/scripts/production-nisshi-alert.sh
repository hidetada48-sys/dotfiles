#!/bin/bash
# 生産日誌（週次）・調査帳（月次）アラート（SessionStart）
# 役割：先週分の生産日誌が未作成／先月分の調査帳が未作成なら耳打ちする。
# 設計思想：事実通知のみ（DB照会・スクリプト実行はしない＝フリーズ防止）。
#           python3非依存の純bash（Linux / Windows git-bash 共通）。出来れば黙る。

PROJECT="$HOME/mino-sakura-hq"

case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac

cd "$PROJECT" || exit 0

# ★ TZ=Asia/Tokyo は使わない（Windows git-bash に tzdata が無く黙って UTC に落ちるため）
TODAY=$(date -u -d '+9 hours' +%Y-%m-%d 2>/dev/null)
[ -n "$TODAY" ] || exit 0
DOW=$(date -u -d '+9 hours' +%u 2>/dev/null)          # 1=月 … 7=日

# --- ① 週次＝先週の日曜まで埋まっているか ---
LAST_SUN=$(date -u -d "${TODAY} -${DOW} day" +%Y-%m-%d 2>/dev/null)
NISSHI="production/reports/生産日誌_${LAST_SUN:0:7}.html"
FILLED=""
[ -f "$NISSHI" ] && FILLED=$(head -c 200 "$NISSHI" | sed -n 's/.*filled_to: \([0-9-]*\).*/\1/p')

if [ -z "$FILLED" ] || [ "$FILLED" \< "$LAST_SUN" ]; then
  echo ""
  echo "========== 生産日誌（週次） =========="
  echo "  先週の日曜（${LAST_SUN}）までが未作成です。"
  [ -n "$FILLED" ] && echo "  いまの ${NISSHI} は ${FILLED} まで。"
  echo "  → 専務に「${LAST_SUN}までの生産数量をDBから取ります」と伝え、承認を得てから実行する。"
  echo "  手順：python production/scripts/nisshi.py --month ${LAST_SUN:0:7} --to ${LAST_SUN}"
  echo "        python tools/report_html.py --all → A4縦1枚のHTML URLだけを提示"
  echo "======================================"
  echo ""
fi

# --- ② 月次＝先月分の調査帳 ---
THIS_MONTH=${TODAY:0:7}
TARGET=$(date -u -d "${THIS_MONTH}-01 -1 day" +%Y-%m 2>/dev/null)
[ -n "$TARGET" ] || exit 0

if [ ! -f "production/reports/調査帳_${TARGET}.html" ]; then
  echo ""
  echo "========== 調査帳（月次） =========="
  echo "  対象月：${TARGET}分（暦月）／未作成"
  echo "  → 専務に次の2つをおたずねし、回答を受けてから作成する（自動では取らない）。"
  echo "     〔1〕${TARGET} の原料使用量（kg）"
  echo "     〔2〕${TARGET} の原料仕入（kg）"
  echo "     ※生産高・袋数はDBから、煮釜回数は原料水量水温.xlsx から自動。ジャンボは重量集計から足す。"
  echo "  手順：python production/scripts/nisshi.py --chosa ${TARGET} --shiyou <使用量> --shiire <仕入> --kurikoshi <前月繰越>"
  echo "        python tools/report_html.py --all → A4横1枚のHTML URLだけを提示"
  echo "===================================="
  echo ""
fi
