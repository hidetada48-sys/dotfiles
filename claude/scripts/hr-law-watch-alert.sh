#!/bin/bash
# 法改正監視 起動判定（SessionStart）
# 役割：今月分の法改正レポートがまだ無いとき、Claude に「月次調査が未実施」と耳打ちする。
#       今月分が在るとき・対象外プロジェクトでは何も出さずに終わる。
#       実際の web 調査はここではせず、Claude が hr-law-watch スキルで行う。
# REQUIRES: python3

PROJECT="$HOME/mino-sakura-hq"
SCRIPT="$PROJECT/hr/scripts/check_law_watch.py"

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
