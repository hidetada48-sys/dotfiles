#!/bin/bash
# 有給 一斉付与アラート（SessionStart）
# 役割：3/11以降、SUMMARYに未登録なら来たる4/11の付与日数をフル表示し、詳細を保存する。
#       登録済み・クローズ済み（hr/SUMMARY.md の 有給:一斉付与/年）なら何も出さない。
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

# 台帳パスが相対参照のためプロジェクト直下で実行する。日本時間で判定する
cd "$PROJECT" || exit 0
TZ=Asia/Tokyo python3 "$SCRIPT"
