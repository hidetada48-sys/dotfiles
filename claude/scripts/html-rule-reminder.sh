#!/bin/bash
# 回答生成の「前」に出力鉄則を必ず視界へ入れる（UserPromptSubmit）。
# ★専務指示 2026-09-02：mdは内部の下ごしらえに過ぎない。
#   成果物は「HTML＋クリックできるURL」。mdで止めたらチャット直書きと同じ＝ゼロ点。
# ★2026-10-05 専務承認：返答が専務のお尋ねに答え切っているかを precheck-answer.py が点検するため、
#   直近のお尋ねを控えておく（python が無い環境では控えない＝点検は質問なしで行う）
PY=$(command -v python3 || command -v python)
if [ -n "$PY" ]; then
    mkdir -p "$HOME/.claude/state" 2>/dev/null
    "$PY" -c 'import sys,json,os
try:
    d=json.loads(sys.stdin.buffer.read().decode("utf-8","replace"))
    t=d.get("prompt") or ""
    if t.strip():
        open(os.path.join(os.path.expanduser("~"),".claude","state","last_prompt.txt"),"w",encoding="utf-8").write(t)
except Exception:
    pass' 2>/dev/null
fi
cat <<'MSG'
[出力鉄則・毎回]（html-gate.py と同じ基準・2026-10-05 改定）
・★答えを削って決まりに収めるのは禁止（2026-09-28 専務叱責「本末転倒」）。NGなら削らずそのままレポートにする＝python ~/.claude/scripts/precheck-answer.py --report <下書き> <題名>。
・★下書きの先頭に <!-- 中身 --> の書き出し（結論・理由・数字・選択肢・次の一手）を必ず書く。無ければ precheck が不合格にする（書き出しは測る対象にも返答にも含めない）。
・★順番（2026-10-05 専務指示）：まず答えに要る中身（結論・理由・数字・選択肢・次の一手）を全部決めて下書きにする→測る→チャットかレポートかが決まる。「チャットで済ませよう」と先に決めて短く書かない。聞かれた一言だけに答えて残りを次の質問に回さない。
・基準（リンクの有無で分けない）：空行とURLを除いて10行超 か 300字超、または箇条書き・表の行が5行以上ならレポートにしてリンクで出す。
・リンク（8830・8831）を出す返答は結論・リンク・伺い。同じ基準（URLを除き10行・300字）で測る（旧3行・120字は 2026-10-05 廃止）。
　レポートの中身（要点・理由・直し方）は書き写さない。報告そのものの数字は書いてよい（2026-09-30 数字の見張りは廃止）。
・チャットに出す返答は1行でも全部、先に下書きを書いて python ~/.claude/scripts/precheck-answer.py <下書き> で数え、OKの下書きを一字も変えずにそのまま出す（測ったあとに言い直すと「数えずに出した」になる）。
・見張りは画面に何も出さず記録だけ残す。違反は次の指示のときにここに出る。言い直しの一言は出さない。
MSG

PENDING="$HOME/.claude/state/html-gate_pending.log"
if [ -s "$PENDING" ]; then
    echo ""
    echo "[前の返答の違反]（専務の画面には出ていない。同じ破り方をしないこと）"
    while IFS= read -r line; do echo "  - $line"; done < "$PENDING"
    rm -f "$PENDING" 2>/dev/null
fi
exit 0
