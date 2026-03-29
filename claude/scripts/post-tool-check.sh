#!/bin/bash
# PostToolUse Hook: .py・.jsonファイルの構文チェック
# Edit/Write/MultiEdit実行後に自動発火する

# stdinからツール情報（JSON）を読み込む
INPUT=$(cat)

# ツール名を取得
TOOL_NAME=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('tool_name', ''))
except:
    print('')
" 2>/dev/null)

# Edit・Write・MultiEdit以外はスキップ
if [[ "$TOOL_NAME" != "Edit" && "$TOOL_NAME" != "Write" && "$TOOL_NAME" != "MultiEdit" ]]; then
    exit 0
fi

# 対象ファイルパスを取得
FILE_PATH=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('file_path', ''))
except:
    print('')
" 2>/dev/null)

# ファイルパスが空またはファイルが存在しない場合はスキップ
[ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ] && exit 0

# .pyファイル: Python構文チェック
if [[ "$FILE_PATH" == *.py ]]; then
    RESULT=$(python3 -m py_compile "$FILE_PATH" 2>&1)
    if [ $? -ne 0 ]; then
        echo "[構文エラー] $FILE_PATH"
        echo "$RESULT"
        exit 1
    fi
fi

# .jsonファイル: JSON構文チェック
if [[ "$FILE_PATH" == *.json ]]; then
    RESULT=$(python3 -m json.tool "$FILE_PATH" > /dev/null 2>&1)
    if [ $? -ne 0 ]; then
        echo "[JSON構文エラー] $FILE_PATH"
        python3 -m json.tool "$FILE_PATH" 2>&1
        exit 1
    fi
fi

exit 0
