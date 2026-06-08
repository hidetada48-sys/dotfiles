#!/usr/bin/env python3
# UserPromptSubmitフック本体
# プロンプトに「記憶して」が含まれていたら、basic-memoryへの保存を促すリマインドを出す。
import json
import sys

# UserPromptSubmitでstdinに渡されるJSONを読む
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

prompt = data.get("prompt", "")

# 「記憶して」を検知したらリマインドを出力（stdoutがClaudeのコンテキストに渡る）
if "記憶して" in prompt:
    print(
        "[記憶] mcp__basic-memory__write_note を使ってbasic-memoryに保存してください。"
        "auto-memoryシステムは使わないこと。"
    )

sys.exit(0)
