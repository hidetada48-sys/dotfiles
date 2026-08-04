#!/bin/bash
# 月次データ催促アラート（SessionStart）
# 役割：薬品・生産重量・原料日誌・電気代の「最新月」が未着なら耳打ちする。
#       販売実績は既存の sales-monthly-alert.sh が担当するため、ここでは扱わない
#       （二重に鳴らさない）。
# 設計：docs/plans/2026-08-04-月次データ催促-design.md
# 設計思想：事実通知のみ（web調査・pull・重い処理はしない＝フリーズ防止）。
#           判定は中身読み取りが要るため Python に委譲する（xls は bash で読めない）。
#           そろえば静かに終了（済＝黙る）。そろうまで出し続ける。

PROJECT="$HOME/mino-sakura-hq"

# このプロジェクト内で起動したときだけ動く
case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac

cd "$PROJECT" || exit 0

# Windows は python / Linux は python3。見つからなければ黙って降りる
# （誤って「未着」と鳴らさない。労務アラート3本が python3 固定で Windows では
#   鳴っていなかった前例があるため、両方を探す）
PY=$(command -v python || command -v python3)
[ -n "$PY" ] || exit 0

"$PY" production/scripts/check_monthly_data.py 2>/dev/null
