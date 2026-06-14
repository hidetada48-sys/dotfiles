#!/bin/bash
# 年次イベント自動通知（SessionStart）
# 役割：労務の年次イベント（労働保険更新・算定基礎届・人事考課・年末調整・36協定など）が
#       通知窓に入り、まだ hr/SUMMARY.md に未登録のものを耳打ちする。
#       登録済み・窓外のときは何も出さずに終わる。
# REQUIRES: python3

PROJECT="$HOME/mino-sakura-hq"
SCRIPT="$PROJECT/hr/scripts/check_annual_events.py"

# このプロジェクト内で起動したときだけ動く（他プロジェクトでは何もしない）
case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac

# スクリプトが無ければスキップ
[ -f "$SCRIPT" ] || exit 0

# python3 が無い環境（未インストール等）はスキップ
command -v python3 >/dev/null 2>&1 || exit 0

# 日本時間で判定する
TZ=Asia/Tokyo python3 "$SCRIPT"
