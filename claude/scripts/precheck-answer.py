# -*- coding: utf-8 -*-
"""回答を出す前の長さチェック（専務指示 2026-09-19・全リポジトリ共通）。

Stopフックの HTML関門（~/.claude/scripts/html-gate.py）は、回答を画面に出し終えた後にしか動かない。
出してから差し戻されても意味がないため、長くなりそうな回答は下書きをファイルに書き、
このスクリプトで同じ基準を先に当ててから出す。

基準は html-gate.py と同じ（あればそこから読み込む＝基準を二重に持たない）：
  空行を除く行数が10超、または空白・改行を除く文字数が300超 で、
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
        return 10, 300


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
            nd = 0   # 数字の見張りは 2026-09-30 専務決定（案A）で廃止
            ll, lc = m.LINK_LINE_LIMIT, m.LINK_CHAR_LIMIT
        except Exception:
            nl, nc, nd, ll, lc = len(lines), chars, 0, 3, 120
        print(f"（リンクあり）URLを除く本文 行数 {nl}/{ll}　文字数 {nc}/{lc}")
        if nl <= ll and nc <= lc and nd == 0:
            print("OK：このまま出してよい")
            return 0
        print("NG：レポートがあるのに本文が長い。結論1行・リンク1行・伺い1行だけにし、理由・直し方は書き写さない")
        print("  ★チャットから外す数字・理由は、レポートの中に書いてあるかを確かめる。無ければレポートに足してから外す（黙って捨てない）")
        return 1
    try:                                                   # 箇条書き・表の一覧はレポート（html-gate.py と同じ基準・2026-09-24）
        spec = importlib.util.spec_from_file_location("html_gate", GATE)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        nb, lim = m.bullet_lines(msg), m.BULLET_LIMIT
    except Exception:
        nb, lim = 0, 2
    if nb >= lim:
        print(f"NG：箇条書き・表の一覧が {nb} 行ある。一覧はレポートにする（削って収めるのは禁止）：")
        print("  python ~/.claude/scripts/precheck-answer.py --report <下書き> <題名>")
        return 1
    if len(lines) <= line_limit and chars <= char_limit:
        print("OK：このまま出してよい")
        return 0
    print("NG：レポートにする（削って収めるのは禁止）。次で下書きをそのままレポートにする：")
    print("  python ~/.claude/scripts/precheck-answer.py --report <下書き> <題名>")
    return 1


def dead_links(msg):
    """下書きの中のリンクのうち、開けないものを [(URL, 理由)] で返す（2026-09-29 専務指摘
    「エクセルをリンクで開けるかのように提示するが、全て開けませんとなっている」）。
    8831（エクセル）は受付と同じ判定 tools/xlsx_opener.openable() で確かめる＝叩くとエクセルが開くので叩かない。
    8830（レポート）は配信サーバーに実際に取りに行く。受付・サーバーが止まっているときも「開けない」とする"""
    import re
    import urllib.parse
    import urllib.request
    bad = []
    urls = re.findall(r"\]\((http://127\.0\.0\.1:883[01]/[^)]+)\)", msg)   # [題名](URL) は ) まで＝空白を含んでも切らない
    rest = re.sub(r"\]\(http://127\.0\.0\.1:883[01]/[^)]+\)", "", msg)
    urls += re.findall(r"http://127\.0\.0\.1:883[01]/[^)\s>\]]+", rest)   # 素のURL
    repo = next((d for d in [Path.cwd(), *Path.cwd().parents] if (d / "tools/xlsx_opener.py").exists()),
                Path.home() / "mino-sakura-hq")
    for u in urls:
        if ":8831/" in u:
            q = urllib.parse.urlparse(u).query
            rel = (urllib.parse.parse_qs(q).get("f") or [""])[0]
            try:
                spec = importlib.util.spec_from_file_location("xlsx_opener", repo / "tools/xlsx_opener.py")
                m = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(m)
                code, title, why, _ = m.openable(rel)
            except Exception as e:
                code, why = 0, f"受付の判定を読めない（{e}）"
            if code != 200:
                bad.append((u, why))
        else:
            pu = urllib.parse.urlparse(u)
            safe = urllib.parse.urlunparse(pu._replace(path=urllib.parse.quote(urllib.parse.unquote(pu.path)), fragment=""))
            try:
                urllib.request.urlopen(safe, timeout=5)
            except Exception as e:
                bad.append((u, f"レポートが開けない（{e}）"))
    return bad


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


NG_DIR = Path.home() / ".claude/state/precheck_ng"
TRIM_WINDOW_MIN = 30          # NG のあとこの分数のうちに出た、より短い似た下書きは「削って通そうとした」とみなす


def _flat(msg):
    return "".join(msg.split())


def record_ng(path):
    """NG になった下書きを控える＝このあと削って通そうとしたかを見分けるため（2026-09-28）"""
    import datetime
    NG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = f"{datetime.datetime.now():%Y%m%d%H%M%S}"
    (NG_DIR / f"{stamp}.txt").write_text(Path(path).read_text(encoding="utf-8"), encoding="utf-8")
    for old in sorted(NG_DIR.glob("*.txt"))[:-20]:          # 直近20件だけ残す
        old.unlink()


def trimmed_from_ng(path):
    """直前に NG だった下書きを削って短くしたものか（2026-09-28 専務叱責「文字数を抑えるのは本末転倒」）。
    削ってから通すと、長さだけを数える関門は合格してしまう＝削る方向へ流れる。NG のあとは レポートにする道しか認めない"""
    import datetime
    import difflib
    new = _flat(Path(path).read_text(encoding="utf-8"))
    now = datetime.datetime.now()
    for f in sorted(NG_DIR.glob("*.txt"), reverse=True) if NG_DIR.exists() else []:
        try:
            t = datetime.datetime.strptime(f.stem, "%Y%m%d%H%M%S")
        except ValueError:
            continue
        if (now - t).total_seconds() > TRIM_WINDOW_MIN * 60:
            break
        old = _flat(f.read_text(encoding="utf-8"))
        if len(new) < len(old) and difflib.SequenceMatcher(None, old, new).ratio() >= 0.5:
            return f.name
    return None


def to_report(path, title):
    """下書きをそのままレポート（HTML）にして、チャットに出す3行の型を表示する。
    削らずに済むよう、レポートにする手間をゼロにする（2026-09-28）"""
    import datetime
    import re
    import subprocess
    here = Path.cwd()
    repo = next((d for d in [here, *here.parents] if (d / "tools/report_html.py").exists()),
                Path.home() / "mino-sakura-hq")
    safe = re.sub(r'[\\/:*?"<>|\s]+', "_", title).strip("_") or "回答"
    rel = f"private/answers/{datetime.datetime.now():%Y-%m-%d_%H%M}_{safe}.md"
    out = repo / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    body = Path(path).read_text(encoding="utf-8")
    head = "" if body.lstrip().startswith("# ") else "# " + title + "\n\n"
    out.write_text(head + body, encoding="utf-8")
    py = "python" if sys.platform == "win32" else "python3"
    r = subprocess.run([py, "tools/report_html.py", rel], cwd=repo, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    url = "http://127.0.0.1:8830/" + rel[:-3] + ".html"
    ok = (repo / ".reports_html" / (rel[:-3] + ".html")).exists()
    print(("OK：レポートにした " if ok else "NG：HTMLにできなかった ") + str(out))
    if not ok:
        print(r.stdout[-500:], r.stderr[-500:])
        return 1
    print("チャットに出すのは次の3行（結論・リンク・伺い。レポートの中身は書き写さない）：")
    print("  1行目：結論")
    print(f"  2行目：[{title}]({url})")
    print("  3行目：伺い")
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--report":
        sys.exit(to_report(sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else "回答"))
    bad = dead_links(Path(sys.argv[1]).read_text(encoding="utf-8")) if len(sys.argv) >= 2 else []
    if bad:   # 開けないリンクを開けるかのように出さない（削った・削らないとは別の話なので NG の控えには残さない）
        print("NG：開けないリンクがある。リンク先を直して（合格印・置き場・配信）から出す：")
        for u, why in bad:
            print(f"  {u}")
            print(f"    → {why}")
        sys.exit(1)
    rc = main()
    if rc == 0 and len(sys.argv) >= 2:
        ng = trimmed_from_ng(sys.argv[1])
        if ng:
            print(f"NG：直前に NG だった下書き（{ng}）を削って通そうとしている。削って収めるのは禁止＝レポートにする：")
            print("  python ~/.claude/scripts/precheck-answer.py --report <下書き> <題名>")
            print("  ★削ったのが本当に不要な重複だけなら、NG だった元の下書きをそのままレポートにする")
            rc = 1
        else:
            record_ok(sys.argv[1])
    elif rc == 1 and len(sys.argv) >= 2:
        record_ng(sys.argv[1])
    sys.exit(rc)
