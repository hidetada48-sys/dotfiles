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
# ★2026-09-02 修正（Windowsで一度も鳴っていなかった件）
#   ・Windowsの `python3` は Microsoft Store のダミーで、スクリプトを実行しても
#     何も返さない → 判定結果が空＝合格扱いで素通りしていた。
#     そこで「実際に動くpython」を選ぶ方式（report-html-refresh.sh と同じ）に変更。
#   ・git-bash のパス（/c/Users/…）は Windows の python が開けないため cygpath で変換。
#   ・pythonが1つも見つからない場合は「黙って通す」のをやめ、警告して止める（fail-loud）。
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
[ -f "$JUDGE" ] || exit 0

# --- 診断ログ：Stopフックが実際に渡してくる中身を1件だけ保存（原因調査用）---
mkdir -p "$HOME/.claude/state" 2>/dev/null
printf '%s' "$INPUT" > "$HOME/.claude/state/html-gate_payload.json" 2>/dev/null

mkdir -p "$STATE_DIR" 2>/dev/null

# --- 実際にスクリプトを動かせる python を選ぶ（Windowsは python 優先）---
IS_WIN=0
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) IS_WIN=1; ORDER="python py python3" ;;
  *)                    ORDER="python3 python" ;;
esac

PY=""
for c in $ORDER; do
    if command -v "$c" >/dev/null 2>&1 && [ "$("$c" -c 'print(1)' 2>/dev/null)" = "1" ]; then
        PY="$c"; break
    fi
done

# Windowsのpythonは git-bash 形式のパスを開けないのでWindows形式へ変換
JUDGE_ARG="$JUDGE"
if [ "$IS_WIN" = "1" ] && command -v cygpath >/dev/null 2>&1; then
    JUDGE_ARG="$(cygpath -w "$JUDGE")"
fi

# --- pythonが無い＝判定不能。黙って通さず、止めて知らせる（1プロンプト1回だけ）---
if [ -z "$PY" ]; then
    NOPY_FILE="$STATE_DIR/html-gate_nopython.count"
    N=0
    [ -f "$NOPY_FILE" ] && N=$(cat "$NOPY_FILE" 2>/dev/null)
    case "$N" in ''|*[!0-9]*) N=0 ;; esac
    N=$((N + 1)); echo "$N" > "$NOPY_FILE"
    [ "$N" -gt 1 ] && exit 0
    cat >&2 <<'MSG'
[HTML鉄則] 関門が判定できません（動作するpythonが見つからない）。
このままではHTML鉄則が無検査で素通りします。python を用意するか、
回答は必ず「結論1行＋要点3〜5行＋レポートURL」の形で自主的に守ってください。
※この関門は ~/.claude/scripts/html-gate.sh
MSG
    exit 2
fi
rm -f "$STATE_DIR/html-gate_nopython.count" 2>/dev/null

RESULT=$(printf '%s' "$INPUT" | "$PY" "$JUDGE_ARG" 2>/dev/null)
VERDICT=$(printf '%s' "$RESULT" | cut -f1)
KEY=$(printf '%s' "$RESULT" | cut -f2)
[ "$VERDICT" != "block" ] && exit 0

# --- 無限ループ防止：同一プロンプトで2回まで ---
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
md に書いて report_html.py で変換し、[題名](http://127.0.0.1:8830/…) の
リンク付きURLだけをチャットに出すこと（中身の平文貼り付けは違反）。
チャットに残すのは 結論1行＋要点3〜5行＋リンク。
※この関門は ~/.claude/scripts/html-gate.sh（past_mistakes M-013・M-015）
MSG
exit 2
