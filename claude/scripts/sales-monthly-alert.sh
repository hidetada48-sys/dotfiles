#!/bin/bash
# 月次 売上整理アラート（SessionStart）
# 役割：20日締めに合わせ「直近で締まった月」の得意先別売上エクセル整理が未実施なら、
#       専務に「生データをドライブに置いてください」とだけ耳打ちする。
# 設計思想：事実通知のみ（web調査・pull・スクリプト実行はしない＝フリーズ防止）。
#           python3非依存の純bash（Linux / Windows git-bash 共通）。
#           対象月のレポートが1つでも在れば静かに終了（済＝黙る）。やるまで出し続ける。

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

# --- 済／未の判定（ファイル有無） ---
# 対象月の月次レポートが1つでも在れば「済」→静かに終了
FOUND=$(find sales/reports -name "*_月次レポート_${TARGET}.xlsx" 2>/dev/null | head -1)
[ -n "$FOUND" ] && exit 0

# --- 未：専務がやること（生データをドライブに置く）だけ耳打ち ---
echo ""
echo "========== 月次 売上整理（20日締め）=========="
echo "  ${TARGET}分（${START_M}/21〜${END_M}/20）の得意先別売上データが未整理です。"
echo "  → ドライブに生データを置いてください。あとはこちらで整理します。"
echo "============================================"
echo ""
