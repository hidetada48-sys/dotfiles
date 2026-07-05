#!/bin/bash
# 月次 売上整理アラート（SessionStart）
# 役割：20日締めに合わせ「直近で締まった月」の月次整理が未完なら耳打ちする。
#       2段階で判定：①得意先別の月次レポート(xlsx) ②全社横断の月次分析サマリー(HTML)。
#       ①未→「生データをドライブに置いて」／①済②未→「サマリーHTML作成が残り」。
# 設計思想：事実通知のみ（web調査・pull・スクリプト実行はしない＝フリーズ防止）。
#           python3非依存の純bash（Linux / Windows git-bash 共通）。
#           ①②が両方そろえば静かに終了（済＝黙る）。両方そろうまで出し続ける。

PROJECT="$HOME/mino-sakura-hq"

# このプロジェクト内で起動したときだけ動く
case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac

cd "$PROJECT" || exit 0

# --- 対象月の算出（日本時間・20日締め） ---
# 日が21以上 → 今月20日で締まった＝対象月は今月
# 日が20以下 → まだ今月20日前＝直近で締まったのは先月20日＝対象月は先月
TODAY=$(TZ=Asia/Tokyo date +%Y-%m-%d)
DAY=$(TZ=Asia/Tokyo date +%d)
THIS_MONTH=$(TZ=Asia/Tokyo date +%Y-%m)

if [ "$((10#$DAY))" -ge 21 ]; then
  TARGET="$THIS_MONTH"
else
  # 先月 = 今月1日の前日の年月
  TARGET=$(TZ=Asia/Tokyo date -d "${THIS_MONTH}-01 -1 day" +%Y-%m 2>/dev/null)
fi

# date -d が使えない環境では誤検知を避けて黙って降りる
[ -n "$TARGET" ] || exit 0

# 表示用の期間（先月21日〜対象月20日）
END_M=$((10#${TARGET#*-}))
START_M=$((END_M - 1)); [ "$START_M" -eq 0 ] && START_M=12

# --- 済／未の判定（2段階・ファイル有無） ---
# 段階①：得意先別の月次レポート(xlsx)が1つでも在るか（＝生データ取込・分析が済んだ印）
XLSX=$(find sales/reports -name "*_月次レポート_${TARGET}.xlsx" 2>/dev/null | head -1)
# 段階②：全社横断の月次分析サマリー(HTML)が在るか（＝月次フローの仕上げが済んだ印）
SUMMARY=$(find sales/reports -name "月次分析サマリー_${TARGET}.html" 2>/dev/null | head -1)

# 両方そろっていれば「済」→静かに終了。片方でも欠けていれば催促する。
[ -n "$XLSX" ] && [ -n "$SUMMARY" ] && exit 0

echo ""
echo "========== 月次 売上整理（20日締め）=========="
echo "  対象月：${TARGET}分（${START_M}/21〜${END_M}/20）"
if [ -z "$XLSX" ]; then
  # 段階①未：専務がやること（生データをドライブに置く）だけ耳打ち
  echo "  得意先別売上データが未整理です。"
  echo "  → ドライブに生データを置いてください。あとはこちらで整理します。"
else
  # 段階②未：xlsxは作成済みだが、全社横断の月次分析サマリーHTMLがまだ
  echo "  得意先別の月次レポート(xlsx)は作成済みですが、"
  echo "  月次分析サマリー（全社横断1枚HTML）が未作成です。"
  echo "  → 月次フローの仕上げ（サマリーHTML作成）が残っています。"
fi
echo "============================================"
echo ""
