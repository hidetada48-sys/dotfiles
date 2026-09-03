#!/bin/bash
# ジャンボ（重量売り 119・129）月次 重量集計アラート（SessionStart）
# 役割：暦月で締まった先月分の重量集計レポートが未作成なら耳打ちする。
#       専務の承認を得てから業務DBを引く（無断取得は禁止＝CLAUDE.md 大原則）。
# 設計思想：事実通知のみ（DB照会・スクリプト実行はしない＝フリーズ防止）。
#           python3非依存の純bash（Linux / Windows git-bash 共通）。
#           レポートが出来れば黙る。出来るまで出し続ける（＝月初に取りこぼさない）。

PROJECT="$HOME/mino-sakura-hq"

case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac

cd "$PROJECT" || exit 0

# --- 対象月＝先月（暦月）---
# ★ TZ=Asia/Tokyo は使わない（Windows git-bash に tzdata が無く黙って UTC に落ちるため）。
#    UTC に +9時間して明示的に JST を作る。
THIS_MONTH=$(date -u -d '+9 hours' +%Y-%m 2>/dev/null)
[ -n "$THIS_MONTH" ] || exit 0
TARGET=$(date -u -d "${THIS_MONTH}-01 -1 day" +%Y-%m 2>/dev/null)
[ -n "$TARGET" ] || exit 0

# 済み（レポートが在る）なら黙る
[ -f "sales/reports/ジャンボ重量集計_${TARGET}.md" ] && exit 0

echo ""
echo "========== ジャンボ（119・129）重量集計 =========="
echo "  対象月：${TARGET}分（暦月）／レポート未作成"
echo "  商品119=ジャンボ芯無し130S・商品129=ジャンボ100S（川）。ケースでなく重量(kg)売り。"
echo "  出すもの：売上日ごとの合計重量(kg)と、歩留り0.94を掛けた製品重量。"
echo ""
echo "  → 専務に次の3点を確認し、承認を得てから業務DBを引くこと（無断取得は禁止）。"
echo "     〔0〕${TARGET}分の売上を これから上げる予定はあるか？"
echo "          ある → 集計はしない（専務が売上を上げてから指示をもらう）"
echo "     〔A〕${TARGET}の 1〜7日 の売上は本当に ${TARGET} の生産か？（違えば落とす）"
echo "     〔B〕${THIS_MONTH}の 1〜7日 の売上は ${TARGET} の生産か？（そうなら足す）"
echo "          ※知りたいのは売上日ではなく生産日。計上が月をまたぐため毎回この2つを確認する。"
echo ""
echo "  手順：python sales/scripts/jumbo_weight_report.py ${TARGET} --probe   ← 確認材料を出す"
echo "        python sales/scripts/jumbo_weight_report.py ${TARGET} [--exclude 日付] [--include 日付]"
echo "        python tools/report_html.py --all → レポートのHTML URLだけを提示"
echo "================================================"
echo ""
