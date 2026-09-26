#!/bin/bash
# 「長い回答をチャットに書いたらHTML化してURLで出す」ルールを機械で強制する関門
#
# 何をするか：
#   Stop フック（Claudeが応答を終える瞬間）で直前の回答テキストを見て、
#   ・本文が長い（空行を除く行数が10超、**または**空白を除く文字数が400超）
#   ・なのにレポートURL（127.0.0.1:8830）が入っていない
#   なら違反として記録する（2026-09-26 から止めない＝画面に警告を出さない。記録は次の指示で
#   html-rule-reminder.sh が Claude にだけ伝える）。
#
# 判定の中身は html-gate.py（同じフォルダ）。例外＝コードブロックを含む回答／
# 直近の専務の指示に「チャットで」「HTML不要」等がある場合は鳴らさない。
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
export PYTHONIOENCODING=utf-8   # 日本語を正しく数える（2026-09-18 cp932で字数が約1.65倍に化けていた）

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

# --- pythonが無い＝判定不能。止めずに記録し、次の指示で Claude に伝える（2026-09-26）---
if [ -z "$PY" ]; then
    printf '%s\t%s\t\n' "$(date '+%Y-%m-%d %H:%M')" "関門が判定できない（動く python が無い）＝返答は自分で3行・120字・数字なしを守る" >> "$STATE_DIR/html-gate_pending.log" 2>/dev/null
    exit 0
fi
rm -f "$STATE_DIR/html-gate_nopython.count" 2>/dev/null

RESULT=$(printf '%s' "$INPUT" | "$PY" "$JUDGE_ARG" 2>/dev/null)
VERDICT=$(printf '%s' "$RESULT" | cut -f1)
KEY=$(printf '%s' "$RESULT" | cut -f2)
NLINES=$(printf '%s' "$RESULT" | cut -f3)
[ "$VERDICT" != "block" ] && exit 0

# ★2026-09-26 変更（専務指示「決まりを守れるよう改善したうえで、警告文は出さない」）：
#   この関門は返答が画面に出た「後」に動く。止める（exit 2）と画面に「Stop hook error」と警告文が出て、
#   会話が続くので Claude がもう一言足し、それも専務の画面に出ていた。止めても読まれた後なので意味が無い。
#   そこで止めずに違反を記録だけし（画面には何も出さない）、次の指示のときに
#   html-rule-reminder.sh が Claude にだけ伝える。守る側の本命は「出す前に precheck-answer.py で数える」。
#   設計＝mino-sakura-hq/docs/plans/2026-09-26-返答の決まりを守る仕組みの改善-design.md
case "$NLINES" in
  B*) WHY="一覧をチャットに書いた（箇条書き・表の行が${NLINES#B}）。一覧はレポートにしてリンクだけ出す" ;;
  P*) WHY="数えずに出した（precheck-answer.py で OK になった下書きと同じ文ではない）" ;;
  L*) R="${NLINES#L}"
      case "$R" in
        *c) WHY="リンク付きなのに本文が${R%c}字（上限120字）" ;;
        *d) WHY="リンク付きなのにリンクの行以外に数字がある行が${R%d}（名前の中の数字も不可）" ;;
        *)  WHY="リンク付きなのに本文が${R}行（上限3行）" ;;
      esac ;;
  *)  WHY="長い返答（${NLINES}）をレポートにせずチャットに書いた" ;;
esac
HEAD=$(printf '%s' "$INPUT" | "$PY" -c 'import sys,json;d=json.loads(sys.stdin.buffer.read().decode("utf-8","replace"));m=d.get("last_assistant_message") or "";print(m.replace(chr(10)," ")[:60])' 2>/dev/null)
REC="$(date '+%Y-%m-%d %H:%M')	${WHY}	${HEAD}"
printf '%s\n' "$REC" >> "$STATE_DIR/html-gate_pending.log" 2>/dev/null     # 次の指示で Claude に伝えて消す
printf '%s\n' "$REC" >> "$STATE_DIR/html-gate_violations.log" 2>/dev/null  # 消さない＝回数を後から数える
exit 0
