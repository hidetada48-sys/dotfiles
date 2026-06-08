#!/usr/bin/env bash
# 引数で渡した.pyスクリプト（または -c "コード"）を「実際に動くpython」で実行する共通ラッパー
# 理由: Windowsの python3 はMicrosoft Storeのスタブ（偽物・exit49）で動かない。
#       Linuxでは python3 が本物のことが多い。両OS対応のため動く実体を探す。
# 使い方: bash run-python.sh /path/to/script.py
#         bash run-python.sh -c "print(123)"
# stdinはexecでそのまま引き継がれる（フックのJSONが本体に届く）。

# WindowsのpythonはI/Oがcp932になり、UTF-8の日本語(stdin/stdout)を取りこぼす。
# UTF-8モードを強制して文字化け・取りこぼしを防ぐ（Linuxでは元々UTF-8なので無害）。
export PYTHONUTF8=1

# python3 → python → py の順で「実際に起動できる」ものを採用する。
# Windowsのpython3スタブは -c "" が失敗するので自動的にスキップされる。
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "" >/dev/null 2>&1; then
    exec "$c" "$@"
  fi
done

# 動くpythonが無ければ素通り（フックを諦める＝誤爆防止）
exit 0
