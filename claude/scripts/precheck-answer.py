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
    # ★2026-10-04 専務「このリンクが開けません」：題名をそのままファイル名にするとURLが長くなり、
    #   ターミナルで折り返されてクリックしても開けない。ファイル名の題名部分は12字までにする（見出しは題名のまま）
    safe = safe[:12].rstrip("_・")
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
    print(f"  2行目：[{safe}]({url})")   # 見出しも短く＝見出しとURLが1行に並んで折り返されないように（2026-10-04）
    print("  3行目：伺い")
    return 0


JARGON = Path(__file__).with_name("jargon_words.txt")


def jargon_hits(msg):
    """私が作った呼び名（jargon_words.txt）が、言い換え（＝）の無い行に出ていれば (語, 行) を返す。
    専務指示 2026-10-02「お前独自の言い回し・単語がふんだんに出てくる。だから言いたいことが入ってこない」"""
    if not JARGON.exists():
        return []
    words = [w.strip() for w in JARGON.read_text(encoding="utf-8").splitlines()
             if w.strip() and not w.lstrip().startswith("#")]
    hits = []
    for line in msg.splitlines():
        if "＝" in line:
            continue
        body = __import__("re").sub(r"\(https?://[^)]*\)|`[^`]*`", "", line)   # URL とファイル名（`…`）は見ない
        for w in words:
            if w in body:
                hits.append((w, line.strip()[:60]))
    return hits


def stop_on_jargon(path):
    hits = jargon_hits(Path(path).read_text(encoding="utf-8"))
    if not hits:
        return False
    print("NG：私が作った呼び名が出ている。専務がふだん使う言葉（商品名・帳票名・個数など）に言い換えるか、")
    print("    同じ行に「＝○○のこと」と言い換えを添えてから出す（~/.claude/scripts/jargon_words.txt）：")
    for w, line in hits[:10]:
        print(f"  「{w}」 … {line}")
    return True


PLAIN_PROMPT = """あなたは、製紙会社の専務に出す業務報告の文章を点検する係です。
読む人は専務（工場の業務と、社内で使っている帳票・日報アプリの画面を知っている経営者）です。
下の「下書き」を1文ずつ読み、専務が1回読んで意味が取れない文、またはオフィシャルな報告書として不適切な文だけを挙げてください。

挙げる文：
〔1〕何を言いたいのかが伝わらない文
〔2〕中身を言わずに言い回しだけで済ませた文＝何と何を比べるのか・誰が何をするのか・何を指すのかが、前後の文を読んでも分からない文
〔3〕報告書として不適切な表現：書き手の作業日誌（何を読んだ・どのファイルを直した・プログラムを流した など）／書き手が独自に付けた呼び名／口語・くだけた言い方・感情的な言い方（「〜っぽい」「ざっくり」「とりあえず」「ちゃんと」「黙って」など）／プログラム名・ファイル名が文の主語

挙げない文：
- 業務の物の名前（製品名 100S・130S、帳票名、日報アプリ、確認画面、切り抜き、品種名、一覧エクセル など）、人や会社の名前、数字は、そのままで分かる言葉として扱う
- 「アプリは〜と答えます」「アプリがお尋ねします」のように、アプリや機械が主語の文は問題にしない（不適切なのはプログラムのファイル名が主語の文）
- 前後の文や表の見出しを読めば中身が分かる文は挙げない
- 迷う文は挙げない。はっきり伝わらない文だけを挙げる

見本（専務が「分からない」と言った文＝挙げる）：
- 「2で区切れないときは、品種ごとの合計のうち計にいちばん近い品種と比べ、その品種の行を聞く」（何と何を比べるのかが分からない）
- 「品種名に頼らない」（何をするのかが分からない）
- 「質問への Gemini の答えでも、品種名が他と違う行があれば必ず書かせる」（誰に何を書かせるのかが分からない）
- 「品種が2つなのに計が1つなので、85,000m を勤全体の計と判断した」（なぜそうなるのかの筋が通らない）
見本（専務が「この日本語が正しい」と言った文＝挙げない）：
- 「確認画面で専務がアプリに質問したとき、品種名がほかの行と違う行があれば、アプリは『1本目だけ角130Sと読んでいます』のように、その行を名指しして答える」
- 「これまで確定した日報に無い品種名を読んだときは、確認画面にその行の紙の切り抜きを出し、『初めて出てきた品種名です。紙に書かれた品種名を入れてください』とお尋ねする」

答えは次の JSON だけを返してください（説明の文は付けない）：
{{"問題": [{{"文": "下書きの文をそのまま", "物差し": "1|2|3", "理由": "なぜ伝わらないか（短く）"}}]}}
問題が無ければ {{"問題": []}}

下書き：
{draft}
"""

PLAIN_CACHE = Path.home() / ".claude" / "state" / "plain-check"


def plain_issues(msg):
    """分かる日本語の点検（2026-10-05 専務承認）。別の Claude に下書きを1文ずつ読ませ、伝わらない文を返す。
    専務指示「この日本語が正しいな　これが claudemd に書かれているんだろ　また守れていない　これも強制的に守れるようにしておけ」
    （「計にいちばん近い品種と比べ」「品種名に頼らない」「必ず書かせる」を報告に書いた）。
    返り値＝(問題の一覧, 点検できなかった理由)。同じ下書きは控えから答える（点検に 20〜40 秒かかるため）"""
    import hashlib, json, re, shutil, subprocess
    text = re.sub(r"\[([^\]]*)\]\((https?://[^)]*)\)", r"\1", msg)        # リンクは題名だけを読ませる
    text = re.sub(r"https?://\S+", "", text).strip()
    if not text:
        return [], ""
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]
    cache = PLAIN_CACHE / f"{h}.json"
    if cache.exists():
        try:
            return json.loads(cache.read_text(encoding="utf-8")), ""
        except Exception:
            pass
    exe = shutil.which("claude")
    if not exe:
        return [], "claude が見つからない"
    lean = ["--setting-sources", "", "--strict-mcp-config", "--no-chrome", "--disable-slash-commands",
            "--no-session-persistence", "--model", "opus", "--tools", ""]   # 設定・フックを読まずに1回だけ答えさせる
    try:
        r = subprocess.run([exe, "-p", *lean, "--output-format", "json"], input=PLAIN_PROMPT.format(draft=text),
                           capture_output=True, text=True, encoding="utf-8", timeout=180)
        res = json.loads(r.stdout or "{}")
        if res.get("is_error"):
            return [], str(res.get("result") or "")[:120]
        body = str(res.get("result") or "")
        m = re.search(r"\{.*\}", body, re.S)
        issues = json.loads(m.group(0)).get("問題", []) if m else None
        if issues is None:
            return [], "点検の答えが読めない"
    except Exception as ex:
        return [], f"{type(ex).__name__}: {ex}"[:120]
    try:
        PLAIN_CACHE.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(issues, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return issues, ""


def stop_on_plain(path):
    """伝わらない文が1つでもあれば NG（チャットにもレポートにも出させない）。点検できないときは知らせて通す"""
    issues, why = plain_issues(Path(path).read_text(encoding="utf-8"))
    if why:
        print(f"注意：分かる日本語の点検ができませんでした（{why}）。出す前に、専務の立場で1文ずつ読み直すこと")
        return False
    if not issues:
        return False
    print("NG：専務に伝わらない文がある。中身（何と何を・誰が何を・いくつ）を書いた文に書き直してから、もう一度測る：")
    for it in issues[:10]:
        print(f"  〔{it.get('物差し', '')}〕「{str(it.get('文', ''))[:70]}」")
        print(f"      → {it.get('理由', '')}")
    return True


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--report":
        if stop_on_jargon(sys.argv[2]):   # レポートにする前に言い換える（呼び名のままレポートにしない）
            sys.exit(1)
        if stop_on_plain(sys.argv[2]):    # 伝わらない文のままレポートにしない（2026-10-05）
            sys.exit(1)
        sys.exit(to_report(sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else "回答"))
    if len(sys.argv) >= 2 and stop_on_jargon(sys.argv[1]):   # 言い換えは削るのとは別＝NG の控えには残さない
        sys.exit(1)
    if len(sys.argv) >= 2 and stop_on_plain(sys.argv[1]):    # 書き直しも削るのとは別＝NG の控えには残さない（2026-10-05）
        sys.exit(1)
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
