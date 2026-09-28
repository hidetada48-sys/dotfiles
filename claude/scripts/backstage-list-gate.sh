#!/bin/bash
# 裏方一覧の見張り（Stop フック・2026-09-28 専務指示）
# 今日、裏方の案件の道具・正典に手を入れたのに、当日の裏方一覧のその行と本体レポートが変わっていなければ
# 応答の終了を差し止め（exit 2）、Claude に直させる。判定の本体は各リポジトリの tools/backstage_list_gate.py。
# リポジトリや python が無い環境では黙って終わる（Windows・Linux 共通）。
# 無限ループ防止：同じセッション×同じ指摘で最大3回まで。

set -u
REPO="$HOME/mino-sakura-hq"
TOOL="$REPO/tools/backstage_list_gate.py"
[ -f "$TOOL" ] || exit 0

INPUT=""
[ ! -t 0 ] && INPUT=$(cat 2>/dev/null)
SESSION=$(printf '%s' "$INPUT" | grep -o '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
[ -z "$SESSION" ] && SESSION="nosession"

OUT=$(bash "$HOME/.claude/hooks/run-python.sh" "$TOOL" </dev/null 2>/dev/null)
[ -z "$OUT" ] && exit 0

# 同じ指摘の繰り返しは3回まで
STATE_DIR="$HOME/.claude/state"
mkdir -p "$STATE_DIR" 2>/dev/null
SIG=$(printf '%s' "$OUT" | cksum | cut -d' ' -f1)
KEY=$(printf '%s' "${SESSION}_${SIG}" | tr -c 'A-Za-z0-9_.-' '_')
COUNT_FILE="$STATE_DIR/backstage-list-gate_${KEY}.count"
N=0
[ -f "$COUNT_FILE" ] && N=$(cat "$COUNT_FILE" 2>/dev/null)
case "$N" in ''|*[!0-9]*) N=0 ;; esac
N=$((N + 1))
echo "$N" > "$COUNT_FILE"
[ "$N" -gt 3 ] && exit 0

echo "$OUT" >&2
exit 2
