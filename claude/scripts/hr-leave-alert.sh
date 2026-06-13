#!/bin/bash
# 有給 一斉付与アラート（SessionStart）
# 役割：3/11以降そのサイクルで初回起動のときだけ、来たる4/11の付与日数を通知する。
#       普段（通知済みサイクル・期日前）は何も出さずに終わる。
# REQUIRES: python3

PROJECT="$HOME/mino-sakura-hq"
SCRIPT="$PROJECT/hr/scripts/check_paid_leave.py"

# このプロジェクト内で起動したときだけ動く（他プロジェクトでは何もしない）
case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac

# スクリプトが無ければスキップ
[ -f "$SCRIPT" ] || exit 0

# python3 が無い環境（未インストール等）はスキップ
command -v python3 >/dev/null 2>&1 || exit 0

# 台帳パスが相対参照のためプロジェクト直下で実行する
cd "$PROJECT" || exit 0
python3 "$SCRIPT"
