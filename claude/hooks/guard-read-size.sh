#!/usr/bin/env bash
# guard-read-size.py を共通ラッパー(run-python.sh)経由で実行する。
# run-python.sh が「動くpython」選択とUTF-8強制(PYTHONUTF8)を行うため、
#   - Windowsのpython3スタブ問題を回避
#   - ブロックメッセージの文字化けを防止（前回固まりの原因だった）
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# execでstdin（PreToolUseのJSON）とexitコード(2=ブロック)をそのまま引き継ぐ
exec bash "$DIR/run-python.sh" "$DIR/guard-read-size.py"
