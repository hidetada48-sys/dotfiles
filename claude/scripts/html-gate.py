#!/usr/bin/env python3
"""html-gate.sh の判定部。Stopフックの入力JSONを標準入力で受け取り、
"block\t<キー>" または "skip\t" を1行出力する。

判定：直前の回答が「長い」のにレポートURLが無ければ block。
　　　長さは **行数（空行除く）と 文字数（空白・改行除く）のどちらか** で測る。
例外：コードブロックを含む／直近の専務の指示が「チャットで」等／URLあり。

★2026-09-02 修正：
  Stopフックの入力JSONには last_assistant_message が含まれない場合がある
  （含まれない環境では判定対象が空＝常にskipになり、関門が一度も鳴らなかった）。
  そのため transcript_path から直近のassistant発話を読む経路を追加した。
"""
import json
import re
import os
import sys

LIMIT = int(os.environ.get("HTML_GATE_LIMIT", "10"))
# ★2026-09-13 追加：行数だけで見ていたため「長い段落を数行」だと素通りしていた
#   （6段落＝6行でも中身は800字、という回答が実際に抜けた＝専務指摘）。
#   文字数でも測る。空白・改行は数えない。
CHAR_LIMIT = int(os.environ.get("HTML_GATE_CHAR_LIMIT", "400"))
# 専務が「チャットで答えろ」と明示した場合は鳴らさない
# ★2026-09-23 追加（専務指示・恒久）：レポートを作ったのにチャットで中身をだらだら書いていた。
#   リンクがあれば無条件合格だった抜け道を塞ぐ。リンクがある回答は、URL部分を除いて
#   行数5・文字数250まで（＝結論1行＋リンク＋判断を仰ぐこと1〜3行）。
LINK_LINE_LIMIT = int(os.environ.get("HTML_GATE_LINK_LIMIT", "5"))
LINK_CHAR_LIMIT = int(os.environ.get("HTML_GATE_LINK_CHAR_LIMIT", "250"))


def body_size(msg):
    """URLを除いた本文の行数・文字数を返す（リンクの長さで鳴らさないため）"""
    t = re.sub(r"\(https?://[^)\s]*\)", "", msg)
    t = re.sub(r"https?://\S+", "", t)
    lines = [l for l in t.split("\n") if l.strip()]
    return len(lines), len("".join(t.split()))


def has_link(msg):
    return "127.0.0.1:8830" in msg or "127.0.0.1:8831/open" in msg


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
        d = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))   # UTF-8で読む（既定のcp932だと日本語が約1.65倍に数えられ、短い回答まで止めていた 2026-09-18）
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
    if has_link(msg):   # レポート（8830）・エクセル（8831）のリンクあり＝本文は短く（2026-09-23）
        nl, nc = body_size(msg)
        if nl <= LINK_LINE_LIMIT and nc <= LINK_CHAR_LIMIT:
            out("skip")
        for kw in SKIP_WORDS:
            if kw in lu:
                out("skip")
        key = str(d.get("prompt_id") or d.get("session_id") or "nokey")[:64]
        # 3列目の先頭 L ＝「リンクはあるが本文が長い」
        sys.stdout.write("block\t" + key + "\tL" + (str(nl) if nl > LINK_LINE_LIMIT else str(nc) + "c") + "\n")
        sys.exit(0)

    lines = [l for l in msg.split("\n") if l.strip()]
    chars = len("".join(msg.split()))          # 空白・改行を除いた文字数
    if len(lines) <= LIMIT and chars <= CHAR_LIMIT:
        out("skip")

    for kw in SKIP_WORDS:
        if kw in lu:
            out("skip")

    # ★2026-09-02 修正（欠陥C）：キーに行数を入れると、行数が変わるたびに
    #   カウンタが別物になり「同一プロンプトで何回ブロックしたか」が積み上がらない。
    #   プロンプト単位で数えるため行数はキーから外し、行数は3列目で渡す。
    key = str(d.get("prompt_id") or d.get("session_id") or "nokey")[:64]
    # 3列目＝鳴った理由。行数超過なら行数、文字数超過なら「Nc」（cはcharsの意）
    size = str(len(lines)) if len(lines) > LIMIT else str(chars) + "c"
    sys.stdout.write("block\t" + key + "\t" + size + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
