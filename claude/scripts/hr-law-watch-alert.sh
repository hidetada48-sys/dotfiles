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

# python3 が無い環境（未インストール等）はスキップ
command -v python3 >/dev/null 2>&1 || exit 0

# 日本時間で判定する
TZ=Asia/Tokyo python3 "$SCRIPT"
