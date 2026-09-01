#!/bin/bash
# 保存3点セットの③記憶（basic-memory）を機械で強制する関門
#
# 何をするか：
#   今日コミットがあるのに basic-memory へノートが1本も書かれていなければ、
#   Stop フック（Claudeが応答を終えようとする瞬間）で exit 2 を返して終了を差し止める。
#   → Claudeは「③記憶が未実施」という指摘を受け取り、write_note するまで会話を終われない。
#
# 使い方（settings.json）：
#   Stop         : bash ~/.claude/scripts/memory-gate.sh          … 差し止め（exit 2）
#   SessionStart : bash ~/.claude/scripts/memory-gate.sh --startup … 前回セッションの取りこぼしを耳打ち（exit 0）
#
# 判定：
#   ・対象リポジトリ（作業repo＋dotfiles）に「今日のコミット」があるか
#   ・basic-memory のノート(.md)に「最新コミット時刻 −30分」より新しいものがあるか
#     （−30分の猶予＝「記憶してからコミットした」順序を誤検知しないため）
# 無限ループ防止：同じセッション×同じコミットで最大3回まで。それ以上は鳴らさない。

set -u

STARTUP=0
[ "${1:-}" = "--startup" ] && STARTUP=1

REPOS=("$HOME/mino-sakura-hq" "$HOME/dotfiles")
MEM_DIR="${MEMORY_GATE_DIR:-$HOME/basic-memory}"   # テスト用に環境変数で差し替え可
STATE_DIR="$HOME/.claude/state"

# basic-memory のノート置き場が無ければ何もしない（環境差で黙って終了）
[ -d "$MEM_DIR" ] || exit 0
command -v git >/dev/null 2>&1 || exit 0

# stdin の JSON から session_id を拾う（無くても動く）
INPUT=""
if [ ! -t 0 ]; then
    INPUT=$(cat 2>/dev/null)
fi
SESSION=$(printf '%s' "$INPUT" | grep -o '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
[ -z "$SESSION" ] && SESSION="nosession"

# --- 今日のコミットのうち最新のもの（epoch秒とハッシュ）を全リポジトリから拾う ---
LATEST_TS=0
LATEST_REF=""
for R in "${REPOS[@]}"; do
    [ -d "$R/.git" ] || continue
    LINE=$(git -C "$R" log -1 --since=midnight --format='%ct %h' 2>/dev/null)
    [ -z "$LINE" ] && continue
    TS=${LINE%% *}
    case "$TS" in ''|*[!0-9]*) continue ;; esac
    if [ "$TS" -gt "$LATEST_TS" ]; then
        LATEST_TS=$TS
        LATEST_REF="$(basename "$R"):${LINE##* }"
    fi
done

# 今日のコミットが無ければ関門は不要
[ "$LATEST_TS" -eq 0 ] && exit 0

# --- basic-memory に「最新コミット −30分」より新しいノートがあるか ---
THRESHOLD=$((LATEST_TS - 1800))
FOUND=$(find "$MEM_DIR" -name '*.md' -newermt "@$THRESHOLD" -print -quit 2>/dev/null)
[ -n "$FOUND" ] && exit 0

MSG="[保存3点セット] ③記憶が未実施です。今日のコミット（${LATEST_REF}）に対して basic-memory のノートが1本もありません。
mcp__basic-memory__write_note で今日の作業を保存してください（専務に「記憶しますか？」と聞かず実行する）。
※この関門は ~/.claude/scripts/memory-gate.sh（past_mistakes M-014）"

# SessionStart は耳打ちのみ（会話を止めない）
if [ "$STARTUP" -eq 1 ]; then
    echo "$MSG"
    exit 0
fi

# --- 無限ループ防止：同一セッション×同一コミットで3回まで ---
mkdir -p "$STATE_DIR" 2>/dev/null
KEY=$(printf '%s' "${SESSION}_${LATEST_REF}" | tr -c 'A-Za-z0-9_.-' '_')
COUNT_FILE="$STATE_DIR/memory-gate_${KEY}.count"
N=0
[ -f "$COUNT_FILE" ] && N=$(cat "$COUNT_FILE" 2>/dev/null)
case "$N" in ''|*[!0-9]*) N=0 ;; esac
N=$((N + 1))
echo "$N" > "$COUNT_FILE"
[ "$N" -gt 3 ] && exit 0

echo "$MSG" >&2
exit 2
