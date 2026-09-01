#!/bin/bash
# 「長い回答をチャットに書いたらHTML化してURLで出す」ルールを機械で強制する関門
#
# 何をするか：
#   Stop フック（Claudeが応答を終える瞬間）で直前の回答テキストを見て、
#   ・本文が10行を超えている（空行除く）
#   ・なのにレポートURL（127.0.0.1:8830）が入っていない
#   なら exit 2 で終了を差し止める。→ レポート化してURLを出すまで会話を終われない。
#
# 判定の中身は html-gate.py（同じフォルダ）。例外＝コードブロックを含む回答／
# 直近の専務の指示に「チャットで」「HTML不要」等がある場合は鳴らさない。
# 無限ループ防止：同一プロンプトで2回まで。
#
# 配線：settings.json の Stop に  bash ~/.claude/scripts/html-gate.sh
# 正典：CLAUDE.md「★回答提示の絶対ルール」／past_mistakes M-013・M-015

set -u

STATE_DIR="$HOME/.claude/state"
JUDGE="$(dirname "$0")/html-gate.py"

INPUT=""
if [ ! -t 0 ]; then
    INPUT=$(cat 2>/dev/null)
fi
[ -z "$INPUT" ] && exit 0
command -v python3 >/dev/null 2>&1 || exit 0   # python無しの環境（Windows等）は黙って終了
[ -f "$JUDGE" ] || exit 0

RESULT=$(printf '%s' "$INPUT" | python3 "$JUDGE" 2>/dev/null)
VERDICT=$(printf '%s' "$RESULT" | cut -f1)
KEY=$(printf '%s' "$RESULT" | cut -f2)
[ "$VERDICT" != "block" ] && exit 0

# --- 無限ループ防止：同一プロンプトで2回まで ---
mkdir -p "$STATE_DIR" 2>/dev/null
SAFE=$(printf '%s' "$KEY" | tr -c 'A-Za-z0-9_.-' '_')
COUNT_FILE="$STATE_DIR/html-gate_${SAFE}.count"
N=0
[ -f "$COUNT_FILE" ] && N=$(cat "$COUNT_FILE" 2>/dev/null)
case "$N" in ''|*[!0-9]*) N=0 ;; esac
N=$((N + 1))
echo "$N" > "$COUNT_FILE"
[ "$N" -gt 2 ] && exit 0

cat >&2 <<'MSG'
[HTML鉄則] いまの回答は本文が10行を超えているのに、レポートURLがありません。
CLAUDE.md「★回答提示の絶対ルール」＝長い回答・表・分類・一覧・複数案の比較は
md に書いて python3 tools/report_html.py で変換し、[題名](http://127.0.0.1:8830/…) の
リンク付きURLだけをチャットに出すこと（中身の平文貼り付けは違反）。
チャットに残すのは 結論1行＋要点3〜5行＋リンク。
※この関門は ~/.claude/scripts/html-gate.sh（past_mistakes M-013・M-015）
MSG
exit 2
