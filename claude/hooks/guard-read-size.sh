#!/usr/bin/env bash
# guard-read-size.py を「実際に動くpython」で実行するラッパー
# 理由: Windowsの python3 はMicrosoft Storeのスタブ（偽物）で動かない。
#       Linuxでは python3 が本物のことが多い。両OS対応のため動く実体を探す。
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# python3 → python → py の順で「実際に起動できる」ものを採用する。
# Windowsのpython3スタブは -c "" が失敗するので自動的にスキップされる。
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "" >/dev/null 2>&1; then
    # execでstdin（PreToolUseのJSON）をそのまま引き継いで実行する
    exec "$c" "$DIR/guard-read-size.py"
  fi
done

# 動くpythonが無ければ素通り（ガードを諦める＝誤爆防止）
exit 0
