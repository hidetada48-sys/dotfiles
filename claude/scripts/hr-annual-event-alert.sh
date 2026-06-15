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

# 動くpythonを探す（python3→python→py）。WindowsのMS Storeスタブは -c "" が失敗するので弾く。
# UTF-8強制でWindowsのcp932による日本語取りこぼしを防ぐ（Linuxでは無害）。
export PYTHONUTF8=1
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "" >/dev/null 2>&1; then PY="$c"; break; fi
done
# 動くpythonが無ければスキップ（誤爆防止）
[ -n "$PY" ] || exit 0

# 日本時間で判定する
TZ=Asia/Tokyo "$PY" "$SCRIPT"
