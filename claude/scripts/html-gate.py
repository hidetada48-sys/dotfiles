#!/usr/bin/env python3
"""html-gate.sh の判定部。Stopフックの入力JSONを標準入力で受け取り、
"block\t<キー>" または "skip\t" を1行出力する。

判定：直前の回答が10行超（空行除く）なのにレポートURLが無ければ block。
例外：コードブロックを含む／直近の専務の指示が「チャットで」等／URLあり。
"""
import json
import os
import sys

LIMIT = int(os.environ.get("HTML_GATE_LIMIT", "10"))
# 専務が「チャットで答えろ」と明示した場合は鳴らさない
SKIP_WORDS = ("チャットで", "HTML不要", "htmlは要らない", "そのまま書", "口頭で", "短く")


def out(verdict, key=""):
    sys.stdout.write(verdict + "\t" + key + "\n")
    sys.exit(0)


def last_user_text(path):
    """トランスクリプトから直近の専務の発話を取り出す（読めなければ空）"""
    if not path or not os.path.exists(path):
        return ""
    text = ""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if e.get("type") != "user":
                    continue
                c = e.get("message", {}).get("content", "")
                if isinstance(c, list):
                    c = "".join(b.get("text", "") for b in c if isinstance(b, dict))
                if isinstance(c, str) and c.strip():
                    text = c
    except Exception:
        return ""
    return text


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        out("skip")

    msg = d.get("last_assistant_message") or ""
    if isinstance(msg, list):  # 配列形式にも一応対応
        msg = "".join(b.get("text", "") for b in msg if isinstance(b, dict))
    if not msg.strip():
        out("skip")
    if "```" in msg:              # コード提示は対象外
        out("skip")
    if "127.0.0.1:8830" in msg:   # レポートURLを出していれば合格
        out("skip")

    lines = [l for l in msg.split("\n") if l.strip()]
    if len(lines) <= LIMIT:
        out("skip")

    lu = last_user_text(d.get("transcript_path") or "")
    for kw in SKIP_WORDS:
        if kw in lu:
            out("skip")

    key = str(d.get("prompt_id") or d.get("session_id") or "nokey")[:64]
    out("block", "%s_%d" % (key, len(lines)))


if __name__ == "__main__":
    main()
