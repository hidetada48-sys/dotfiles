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

# 動くpythonを探す（python3→python→py）。WindowsのMS Storeスタブは -c "" が失敗するので弾く。
# UTF-8強制でWindowsのcp932による日本語取りこぼしを防ぐ（Linuxでは無害）。
export PYTHONUTF8=1
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "" >/dev/null 2>&1; then PY="$c"; break; fi
done
# 動くpythonが無ければスキップ（誤爆防止）
[ -n "$PY" ] || exit 0

# 台帳パスが相対参照のためプロジェクト直下で実行する。日本時間で判定する
cd "$PROJECT" || exit 0
TZ=Asia/Tokyo "$PY" "$SCRIPT"
