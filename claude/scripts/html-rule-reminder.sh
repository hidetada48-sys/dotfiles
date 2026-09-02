#!/bin/bash
# 回答生成の「前」に出力鉄則を必ず視界へ入れる（UserPromptSubmit）。
# ★専務指示 2026-09-02：mdは内部の下ごしらえに過ぎない。
#   成果物は「HTML＋クリックできるURL」。mdで止めたらチャット直書きと同じ＝ゼロ点。
cat <<'MSG'
[出力鉄則・毎回]
成果物は必ず「HTMLのURL」。md止まりはチャット直書きと同じでゼロ点。
回答が「結論1行＋要点3〜5行」に収まらない、または表・一覧・比較・手順・複数案を含むなら、
本文をチャットに書かず、HTML化して [題名](http://127.0.0.1:8830/…) のリンクだけを出す。
（mdは内部の中間物。作ったら必ずHTMLへ変換し、URLの疎通まで確認してから提示する）
迷ったらHTML化。短く済むものはそもそも作らない。
MSG

# --- 前回、関門(html-gate)を解除して終わっていたら必ず知らせる（2026-09-02 欠陥C対策）---
BYPASS="$HOME/.claude/state/html-gate_bypass.log"
if [ -s "$BYPASS" ]; then
    echo ""
    echo "[HTML鉄則・解除の記録] 直前に関門を解除したまま会話を終えています＝ルール違反が残っています。"
    while IFS= read -r line; do echo "  - $line"; done < "$BYPASS"
    echo "  → 該当の回答をレポート化し、URLで出し直すこと。"
    rm -f "$BYPASS" 2>/dev/null
fi
exit 0
