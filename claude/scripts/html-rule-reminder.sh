#!/bin/bash
# 回答生成の「前」に出力鉄則を必ず視界へ入れる（UserPromptSubmit）。
# ★専務指示 2026-09-02：mdは内部の下ごしらえに過ぎない。
#   成果物は「HTML＋クリックできるURL」。mdで止めたらチャット直書きと同じ＝ゼロ点。
cat <<'MSG'
[出力鉄則・毎回]（html-gate.py と同じ基準・2026-09-26 書き直し）
・長い返答（10行超 か 400字超）・一覧（箇条書き・表の行が2つ以上）・比較・手順は、本文を書かずレポートにしてリンクで出す。
・リンク（8830・8831）を出す返答は「結論1行・リンク1行・伺い1行」。URLを除いて3行・合計120字まで。
　リンクの行以外に数字を一切書かない＝「9月」「5x」のような名前の中の数字も不可。
・リンクを出す返答と4行を超える返答は、先に下書きを書いて python ~/.claude/scripts/precheck-answer.py <下書き> で数え、OKの下書きをそのまま出す。
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
