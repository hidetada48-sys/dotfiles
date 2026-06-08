#!/usr/bin/env python3
# Readの巨大ファイル一括読みを物理ブロックするガード
# 目的: M-009①（巨大ファイル丸読みによる固まり）の再発を仕組みで止める
# 仕組み: PreToolUse(matcher=Read)で呼ばれ、stdinのJSONを検査して
#   - offset/limit付き（範囲指定読み）は許可
#   - フル読みかつ100KB超のファイルは exit 2 でブロック
import json
import sys
import os

# Claude CodeがPreToolUseでstdinに渡すJSONを読む
try:
    data = json.load(sys.stdin)
except Exception:
    # 読めなければ素通り（誤爆防止）
    sys.exit(0)

ti = data.get("tool_input", {})
fp = ti.get("file_path", "")

# 範囲指定（offset または limit 指定）の読み方は安全なので許可
if ti.get("limit") or ti.get("offset"):
    sys.exit(0)

LIMIT = 100 * 1024  # 上限100KB

# ファイルサイズが取れなければ素通り（誤爆防止）
try:
    size = os.path.getsize(fp)
except OSError:
    sys.exit(0)

# 上限超のフル読みはブロックし、安全な代替手段を案内する
if size > LIMIT:
    msg = (
        "[ガード] {fp} は {size:,} バイト（上限 {lim:,} バイト）です。"
        "巨大ファイルの一括読み込みは固まりの原因になるためブロックしました。"
        "offset/limit を付けて範囲指定で読むか、Grep / python で必要な集計だけ取得してください。"
    ).format(fp=fp, size=size, lim=LIMIT)
    print(msg, file=sys.stderr)
    sys.exit(2)

sys.exit(0)
