# -*- coding: utf-8 -*-
"""回答を出す前の長さチェック（専務指示 2026-09-19・全リポジトリ共通）。

Stopフックの HTML関門（~/.claude/scripts/html-gate.py）は、回答を画面に出し終えた後にしか動かない。
出してから差し戻されても意味がないため、長くなりそうな回答は下書きをファイルに書き、
このスクリプトで同じ基準を先に当ててから出す。

基準は html-gate.py と同じ（あればそこから読み込む＝基準を二重に持たない）：
  空行を除く行数が10超、または空白・改行を除く文字数が400超 で、
  レポートURL（127.0.0.1:8830）もエクセルのリンク（127.0.0.1:8831/open）も無い → NG
使い方：python ~/.claude/scripts/precheck-answer.py <下書きファイル>
  OK なら exit 0、NG なら exit 1（行数・文字数と直し方を表示）
"""
import importlib.util
import sys
from pathlib import Path

GATE = Path.home() / ".claude/scripts/html-gate.py"


def limits():
    """関門の基準値を読む（読めなければ同じ既定値）"""
    try:
        spec = importlib.util.spec_from_file_location("html_gate", GATE)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.LIMIT, m.CHAR_LIMIT
    except Exception:
        return 10, 400


def main():
    if len(sys.argv) < 2:
        print("使い方：python ~/.claude/scripts/precheck-answer.py <下書きファイル>")
        return 2
    msg = Path(sys.argv[1]).read_text(encoding="utf-8")
    line_limit, char_limit = limits()
    lines = [l for l in msg.split("\n") if l.strip()]
    chars = len("".join(msg.split()))
    has_link = "127.0.0.1:8830" in msg or "127.0.0.1:8831/open" in msg
    code = "```" in msg
    print(f"行数 {len(lines)}/{line_limit}　文字数 {chars}/{char_limit}　リンク {'あり' if has_link else 'なし'}")
    if has_link or code or (len(lines) <= line_limit and chars <= char_limit):
        print("OK：このまま出してよい")
        return 0
    print("NG：削って結論1行＋要点3〜5行に収めるか、本文をレポートにしてリンクだけ出す")
    return 1


if __name__ == "__main__":
    sys.exit(main())
