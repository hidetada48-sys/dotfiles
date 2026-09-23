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
    if code:
        print("OK：このまま出してよい")
        return 0
    if has_link:
        # リンクがあるときは本文を短く（html-gate.py と同じ基準・2026-09-23）
        try:
            spec = importlib.util.spec_from_file_location("html_gate", GATE)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            nl, nc = m.body_size(msg)
            nd = m.digit_lines(msg)
            ll, lc = m.LINK_LINE_LIMIT, m.LINK_CHAR_LIMIT
        except Exception:
            nl, nc, nd, ll, lc = len(lines), chars, 0, 3, 120
        print(f"（リンクあり）URLを除く本文 行数 {nl}/{ll}　文字数 {nc}/{lc}　数字のある行 {nd}/0")
        if nl <= ll and nc <= lc and nd == 0:
            print("OK：このまま出してよい")
            return 0
        print("NG：レポートがあるのに本文が長い。結論1行・リンク1行・伺い1行だけにし、数字・理由・直し方は書き写さない")
        return 1
    if len(lines) <= line_limit and chars <= char_limit:
        print("OK：このまま出してよい")
        return 0
    print("NG：削って結論1行＋要点3〜5行に収めるか、本文をレポートにしてリンクだけ出す")
    return 1


def record_ok(path):
    """OK になった下書きの指紋を残す＝関門（html-gate.py）が「数えてから出したか」を照合する（2026-09-24）"""
    import datetime
    import hashlib
    msg = Path(path).read_text(encoding="utf-8")
    h = hashlib.sha1("".join(msg.split()).encode("utf-8")).hexdigest()
    log = Path.home() / ".claude/state/precheck_ok.txt"
    log.parent.mkdir(parents=True, exist_ok=True)
    old = log.read_text(encoding="utf-8").splitlines()[-199:] if log.exists() else []   # 直近200件だけ残す
    stamp = f"{datetime.datetime.now():%Y-%m-%d %H:%M}"
    log.write_text("\n".join(old + [h + "\t" + stamp]) + "\n", encoding="utf-8")


if __name__ == "__main__":
    rc = main()
    if rc == 0 and len(sys.argv) >= 2:
        record_ok(sys.argv[1])
    sys.exit(rc)
