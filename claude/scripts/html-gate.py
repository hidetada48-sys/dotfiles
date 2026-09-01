#!/usr/bin/env python3
"""html-gate.sh の判定部。Stopフックの入力JSONを標準入力で受け取り、
"block\t<キー>" または "skip\t" を1行出力する。

判定：直前の回答が10行超（空行除く）なのにレポートURLが無ければ block。
例外：コードブロックを含む／直近の専務の指示が「チャットで」等／URLあり。

★2026-09-02 修正：
  Stopフックの入力JSONには last_assistant_message が含まれない場合がある
  （含まれない環境では判定対象が空＝常にskipになり、関門が一度も鳴らなかった）。
  そのため transcript_path から直近のassistant発話を読む経路を追加した。
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


def _text_of(content):
    """message.content（文字列 or ブロック配列）からテキストだけ取り出す"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            b.get("text", "") for b in content
            if isinstance(b, dict) and b.get("type", "text") == "text"
        )
    return ""


def scan_transcript(path):
    """トランスクリプトを1回走査し、(直近のユーザー発話, 直近のassistant発話) を返す"""
    if not path or not os.path.exists(path):
        return "", ""
    user_text, asst_text = "", ""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                t = e.get("type")
                if t not in ("user", "assistant"):
                    continue
                s = _text_of(e.get("message", {}).get("content", "")).strip()
                if not s:
                    continue
                if t == "user":
                    user_text = s
                else:
                    asst_text = s
    except Exception:
        return user_text, asst_text
    return user_text, asst_text


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        out("skip")

    lu, last_asst = scan_transcript(d.get("transcript_path") or "")

    msg = d.get("last_assistant_message") or ""
    if isinstance(msg, list):  # 配列形式にも一応対応
        msg = _text_of(msg)
    if not msg.strip():        # フックが渡してくれない環境＝トランスクリプトから拾う
        msg = last_asst
    if not msg.strip():
        out("skip")
    if "```" in msg:              # コード提示は対象外
        out("skip")
    if "127.0.0.1:8830" in msg:   # レポートURLを出していれば合格
        out("skip")

    lines = [l for l in msg.split("\n") if l.strip()]
    if len(lines) <= LIMIT:
        out("skip")

    for kw in SKIP_WORDS:
        if kw in lu:
            out("skip")

    key = str(d.get("prompt_id") or d.get("session_id") or "nokey")[:64]
    out("block", "%s_%d" % (key, len(lines)))


if __name__ == "__main__":
    main()
