# -*- coding: utf-8 -*-
"""レポートを作った直後に、チャットの答えの型を差し込む（PostToolUse・Bash）。

なぜ：Stopフックの HTML関門は回答を画面に出した「後」にしか動かず、止めても専務はもう読んでいる。
Claude Code には回答の文字を表示前に止める仕組みが無いため、表示前にできる最後の手として、
report_html.py を流した瞬間（＝これから答えを書く直前）に、答えの型と禁止事項を差し込む。
（専務指示 2026-09-24「機械で強制的に守れるようにしろ」。レポートの数字を結論の行に書き写し続けた）

差し込む内容：変換したHTMLのURLを使った3行の型。結論の行・伺いの行に数字を書かない。
関門 html-gate.py も同じ決まり（リンクのある回答は、リンクの行以外に数字があれば止める）で後から検査する。
"""
import json
import re
import sys
import urllib.parse
from pathlib import PurePosixPath


def main():
    try:
        d = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
    except Exception:
        return
    cmd = (d.get("tool_input") or {}).get("command", "") or ""
    if not re.search(r"python3?(\.exe)?\s+\S*report_html\.py", cmd):   # 実際に流したときだけ（文字列として出てくるだけの命令では鳴らさない）
        return
    # 変換した md から、渡すべきHTMLのURLを作る（--all だけなら目次）
    mds = re.findall(r'["\']?([^\s"\']+\.md)["\']?', cmd)
    urls = []
    for m in mds:
        p = m.replace("\\", "/")
        for root in ("mino-sakura-hq/",):
            if root in p:
                p = p.split(root, 1)[1]
        urls.append("http://127.0.0.1:8830/" + str(PurePosixPath(p).with_suffix(".html")))
    link = urls[0] if urls else "http://127.0.0.1:8830/index.html"
    msg = (
        "【レポートを作った＝答えの型を固定（機械の決まり・例外なし）】\n"
        "チャットに書いてよいのは次の3行だけ。数字（日付・金額・重量・件数）を結論と伺いの行に書かない。"
        "理由・直し方・経緯・比較はレポートの中にだけ書く。\n"
        "1行目：結論（数字なし・40字以内）\n"
        f"2行目：[題名]({link})\n"
        "3行目：伺い（数字なし・「レポートの〇〇でよいですか？」の形）\n"
        "これを外すと Stop の関門（html-gate.py）が止める。止められても言い直さない。"
    )
    out = {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}
    sys.stdout.write(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
