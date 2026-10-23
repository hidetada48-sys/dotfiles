# -*- coding: utf-8 -*-
"""回答を出す前の長さチェック（専務指示 2026-09-19・全リポジトリ共通）。

Stopフックの HTML関門（~/.claude/scripts/html-gate.py）は、回答を画面に出し終えた後にしか動かない。
出してから差し戻されても意味がないため、長くなりそうな回答は下書きをファイルに書き、
このスクリプトで同じ基準を先に当ててから出す。

基準は html-gate.py と同じ（あればそこから読み込む＝基準を二重に持たない）：
  空行とURLを除いて行数が10超、または空白・改行を除く文字数が300超、
  または箇条書き・表の行が5行以上 → NG（リンクの有無で分けない＝2026-10-05 専務指示）
使い方：python ~/.claude/scripts/precheck-answer.py <下書きファイル>
  OK なら exit 0、NG なら exit 1（行数・文字数と直し方を表示）
"""
import importlib.util
import os
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
    if "```" in msg:
        print("長さ：チャットで出せる範囲（このあと言葉と中身の点検）")
        return 0
    # ★2026-10-05 専務指示：リンクの有無で基準を分けない（関門 html-gate.py と同じ基準を読み込む）
    #   空行とURLを除いて10行超 または 300字超／箇条書き・表の行が5行以上 → レポートにする
    try:
        spec = importlib.util.spec_from_file_location("html_gate", GATE)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        nl, nc = m.body_size(msg)
        nb, blim = m.bullet_lines(msg), m.BULLET_LIMIT
        line_limit, char_limit = m.LIMIT, m.CHAR_LIMIT
    except Exception:
        lines = [l for l in msg.split("\n") if l.strip()]
        nl, nc, nb, blim, line_limit, char_limit = len(lines), len("".join(msg.split())), 0, 5, 10, 300
    has_link = "127.0.0.1:8830" in msg or "127.0.0.1:8831/open" in msg
    print(f"URLを除く本文 行数 {nl}/{line_limit}　文字数 {nc}/{char_limit}　一覧 {nb}/{blim}行未満　リンク {'あり' if has_link else 'なし'}")
    if nb >= blim:
        print(f"NG：箇条書き・表の一覧が {nb} 行ある。一覧はレポートにする（削って収めるのは禁止）：")
        print("  python ~/.claude/scripts/precheck-answer.py --report <下書き> <題名> <置き場＝業務は参謀名／仕組み／会話>")
        return 1
    if nl <= line_limit and nc <= char_limit:
        print("長さ：チャットで出せる範囲（このあと言葉と中身の点検）")
        return 0
    if has_link:
        print("NG：レポートがあるのに本文が長い。中身はレポートに書き、チャットは結論・リンク・伺いにする")
        print("  ★チャットから外す数字・理由は、レポートの中に書いてあるかを確かめる。無ければレポートに足してから外す（黙って捨てない）")
        return 1
    print("NG：レポートにする（削って収めるのは禁止）。次で下書きをそのままレポートにする：")
    print("  python ~/.claude/scripts/precheck-answer.py --report <下書き> <題名> <置き場＝業務は参謀名／仕組み／会話>")
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
            # ★説明資料は採点に合格した物だけ出す（2026-10-19 専務承認・tools/check_deck.py）。
            #   前に作ったページが配信に残っていても、合格印が今の中身に合わなければ開けない物として扱う
            md = repo / (urllib.parse.unquote(pu.path).lstrip("/")[:-5] + ".md") if pu.path.endswith(".html") else None
            deck = repo / "tools/check_deck.py"
            if md and md.exists() and deck.exists():
                try:
                    spec = importlib.util.spec_from_file_location("check_deck", deck)
                    cd = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(cd)
                    if cd.is_target(md) and not cd.verify(md):
                        bad.append((u, "説明資料の採点に合格していない（python tools/check_deck.py で採点してから出す）"))
                        continue
                except Exception as e:
                    bad.append((u, f"説明資料の採点の確認を読めない（{e}）"))
                    continue
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


# ★2026-10-13 専務叱責「本業に支障をきたさないようルールを徹底しろ」：
#   10/12 にふるさと納税の分析（業務）を回答のフォルダ（private/answers＝GitHub に上げない）に置き、
#   夜に Linux で続きを始めたとき中身が無かった。置き場を毎回必ず指定させ、業務は参謀の分析フォルダ、
#   仕組みの話は設計書のフォルダ（どちらも GitHub で2台に届く）へ置く。回答のフォルダは「その場限りの会話」だけ。
# ★2026-10-14 専務叱責（目次がめちゃくちゃ）：長い答え（伺い・方針の案・作業の状況）を参謀の分析フォルダに
#   置いていたため、全部「分析」として目次に並んだ。長い答えは参謀の「やりとり」フォルダへ置く＝GitHub で
#   2台に届くが目次には載らない。分析フォルダには、専務が後日もう一度開いて使う成果物を作るときだけ置く。
PLACES = {
    "経営": "executive-advisor/やりとり",
    "業界": "intelligence/やりとり",
    "取引先": "clients/やりとり",
    "販売": "sales/やりとり",
    "現場": "production/やりとり",
    "経理": "finance/やりとり",
    "労務": "hr/やりとり",
    "仕組み": "docs/plans",
    "会話": "private/answers",
}
PLACE_HELP = """置き場を必ず指定する（4つ目の引数）。迷ったら「業務か」で決める：
  業務（会社の数字・分析・判断材料・取引先・生産・在庫・ふるさと納税など。専務が後で読み返す・決める物）
    → 経営／業界／取引先／販売／現場／経理／労務（その参謀の「やりとり」フォルダ。GitHub で2台に届く・目次には載らない）
  仕組み（参謀システム・アプリ・決まり・道具の説明や直し方）→ 仕組み（設計書のフォルダ。GitHub で2台に届く）
  会話（お詫び・その場限りの説明で、二度と読み返さない物）→ 会話（回答のフォルダ。GitHub に上げない＝作ったPCにしか残らない）
  例：python ~/.claude/scripts/precheck-answer.py --report <下書き> <題名> 販売"""


def to_report(path, title, place=None):
    """下書きをそのままレポート（HTML）にして、チャットに出す3行の型を表示する。
    削らずに済むよう、レポートにする手間をゼロにする（2026-09-28）。置き場は必ず指定させる（2026-10-13）"""
    import datetime
    import re
    import subprocess
    if place not in PLACES:
        print("NG：レポートの置き場が指定されていない（または一覧に無い）。" + ("指定＝" + place if place else ""))
        print(PLACE_HELP)
        return 1
    body = Path(path).read_text(encoding="utf-8")
    if place == "会話" and re.search(r"(?<![A-Za-z])(SAL|PRD|CLI|FIN|HR|EXE|INT)-\d{3}(?!\d)", body):
        print("NG：案件番号（SAL-004 など）がある＝業務の中身。会話のフォルダには置かない。参謀の分析フォルダを指定する")
        print(PLACE_HELP)
        return 1
    here = Path.cwd()
    repo = next((d for d in [here, *here.parents] if (d / "tools/report_html.py").exists()),
                Path.home() / "mino-sakura-hq")
    safe = re.sub(r'[\\/:*?"<>|\s]+', "_", title).strip("_") or "回答"
    now = datetime.datetime.now()
    if place == "会話":
        # ★2026-10-04 専務「このリンクが開けません」：題名をそのままファイル名にするとURLが長くなり、
        #   ターミナルで折り返されてクリックしても開けない。ファイル名の題名部分は12字までにする（見出しは題名のまま）
        safe = safe[:12].rstrip("_・")
        rel = f"private/answers/{now:%Y-%m-%d_%H%M}_{safe}.md"
    elif place == "仕組み":
        safe = safe[:24].rstrip("_・")
        rel = f"docs/plans/{now:%Y-%m-%d}-{safe}.md"
    else:
        safe = safe[:24].rstrip("_・")
        rel = f"{PLACES[place]}/{now:%Y-%m-%d}_{safe}.md"
    out = repo / rel
    if out.exists():   # 同じ日に同じ題名がある＝上書きしない（見せたレポートを消さない）
        rel = rel[:-3] + f"_{now:%H%M}.md"
        out = repo / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    head ="" if body.lstrip().startswith("# ") else "# " + title + "\n\n"
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
    # 長い答えは「やりとり」＝案件台帳の詳細レポート欄には書かない（書くと保存のときの点検で止まる・2026-10-14）
    return 0


PROSE_MAX = 60   # レポートの地の文の1行の上限（字）


def prose_lines(body):
    """レポートにする下書きのうち、段落になっている行を (行番号, 行) で返す。
    見出し・箇条書き・番号・表・引用・リンクだけの行は対象外。60字を超えるか「。」が2つ以上なら段落とみなす。
    専務指示 2026-10-08「レポートでもだらだら書くな。箇条書きを使ってわかりやすく書け」"""
    import re
    out = []
    for n, l in enumerate(body.splitlines(), 1):
        t = l.strip()
        if not t or re.match(r"^(#|[-*+]\s|\d+[.)．]\s?|[〔(（]?\d+[〕)）]|\||>|---|<!--)", t):
            continue
        plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)        # リンクは見出しの文字だけ数える
        if len(plain) > PROSE_MAX or plain.count("。") >= 2:
            out.append((n, t))
    return out


def stop_on_prose(body):
    bad = prose_lines(body)
    if not bad:
        return False
    print("NG：レポートに段落がある。見出し（結論・原因・直し方・結果など）＋1項目1行の箇条書きに組み直してから、もう一度 --report する")
    print(f"    （見出し・箇条書き・番号・表以外の行で {PROSE_MAX}字超 か「。」が2つ以上。中身は削らず形だけ変える）")
    for n, t in bad[:8]:
        print(f"  {n}行目：{t[:50]}…")
    return True


OPTION_KEYS = ["仕組み", "操作", "画面", "良い点", "弱い点"]   # 案ごとに必ず書く5つ


def thin_options(body):
    """レポートの「案1」「案2」などの見出しごとに、5つの見出し（仕組み・操作・画面・良い点・弱い点）が
    そろっているかを数え、欠けた案を (見出し, 欠けた物) で返す。AI は使わない（待ち時間なし）。
    専務指摘 2026-10-17「これだけの説明で分かるわけがない」「文字数を超えたレポートを利用しているのに何事か」：
    案2を「ショートカットを作る」の一言で出した。各案に5つの見出しが無ければ不合格にする"""
    import re
    lines = body.splitlines()
    heads = [(i, len(m.group(1)), l.strip()) for i, l in enumerate(lines)
             if (m := re.match(r"^\s*(#+)\s", l))]
    out = []
    for k, (i, level, title) in enumerate(heads):
        if not re.match(r"^#+\s*案\s*[0-9０-９一二三四五]", title):
            continue
        end = next((j for j, lv, _ in heads[k + 1:] if lv <= level), len(lines))
        sec = lines[i + 1:end]
        # 行の頭（箇条書き・番号・見出しの印のあと、8字以内）に見出しの言葉があるかを見る
        missing = [key for key in OPTION_KEYS
                   if not any(re.match(r"^\s*(?:[-*+]|#+|\d+[.)．])\s*.{0,8}?" + key, l) for l in sec)]
        if missing:
            out.append((title.lstrip("# ")[:40], missing))
    # 箇条書きで書いた案（「- 案1：…」）も見る。中身＝その行より深く字下げした行（10/17 の最初の稿はこの形だった）
    for i, l in enumerate(lines):
        m = re.match(r"^(\s*)[-*+]\s*\**案\s*[0-9０-９一二三四五]", l)
        if not m:
            continue
        ind = len(m.group(1).expandtabs(4))
        sec = []
        for l2 in lines[i + 1:]:
            if l2.strip() and len(l2) - len(l2.lstrip()) <= ind:
                break
            sec.append(l2)
        if not any(s.strip() for s in sec):   # 子の行が無い＝案を指しているだけの行（「- 案1か案2か」）は見ない
            continue
        missing = [key for key in OPTION_KEYS
                   if not any(re.match(r"^\s*(?:[-*+]|\d+[.)．])\s*.{0,8}?" + key, s) for s in sec)]
        if missing:
            out.append((l.strip().lstrip("-*+ ")[:40], missing))
    return out


def stop_on_thin_options(body):
    bad = thin_options(body)
    if not bad:
        return False
    print("NG：説明の足りない案がある。案ごとに次の5つを見出し（箇条書きの頭）で書いてから、もう一度 --report する：")
    print("    仕組み（何がどう動くか）／専務の毎日の操作（何が変わるか）／画面に出るもの（例の文つき）／良い点／弱い点")
    for title, missing in bad:
        print(f"  「{title}」 … 無い：{'・'.join(missing)}")
    return True


BASIS_RE = __import__("re").compile(r"^\s*根拠\s*[：:]\s*\S", __import__("re").M)


def stop_on_no_basis(inv):
    """書き出しに「根拠」の欄が無ければ NG。AI は使わない。
    専務指摘 2026-10-16「確固たる自信と裏付けのある正確な回答が準備できるのかどうかを図れないのか」：
    「環境を選択」の意味を公式の説明を確かめずに推測で3回答えた。言い切る事柄ごとに、確かめた事実か推測かを先に書かせる"""
    if BASIS_RE.search(inv or ""):
        return False
    print("NG：書き出しに「根拠」の欄が無い。言い切る事柄ごとに、確かめた事実か推測かを書いてから、もう一度測る：")
    print("  根拠：〇〇は確認済み（何で確かめたか）／△△は推測（確かめられるなら確かめる。できなければ本文に「未確認」と書く）")
    return True


ASK_RE = __import__("re").compile(r"^\s*お尋ね\s*[：:]\s*\S", __import__("re").M)


def stop_on_no_ask(inv):
    """書き出しに「お尋ね」の欄が無ければ NG。AI は使わない。
    控え帳 2026-10-21（09:22・09:50・10:18）：専務は最初から A＝体裁・B＝分析と分けて尋ねていたのに、
    私は自分の調べた事柄（26項目の表・案1・案2）から書き始め、3回聞き直させた。
    書く前に、専務が求めていることを専務の言葉・分け方のまま1行書く（2026-10-21 専務承認）"""
    if ASK_RE.search(inv or ""):
        return False
    print("NG：書き出しに「お尋ね」の欄が無い。専務が求めていることを専務の言葉・分け方のまま1行書いてから、もう一度測る：")
    print("  お尋ね：（例）統合したあと、10/20 に決めた総合検証（A＝体裁・B＝分析の深さ）はどうなるか")
    return True


FIG_WORD = __import__("re").compile(r"図|グラフ|チャート|ページ|枚目|[pｐPＰ]\s*\d|\d\s*[pｐPＰ]|点|線|軸|色|曲線|ドット|帯|ひげ")
HOW_WORD = __import__("re").compile(r"意味|読み方|見方|求め方|出し方|計算|何が見える|なにが見える|何がわかる|どう見る|どうやって|どう求め|見えない|とは|何を表|何か|のことか|か[。？?]?\s*$")


def stop_on_figure_question(inv):
    """お尋ねが資料の図・数字の意味・読み方・求め方なら、文字のレポートを作らずに止める（2026-10-23 専務承認）。
    10/23 見本9ページの「大きい点の意味・平均と95%の範囲の求め方」を文字の箇条書きで答え、
    「さぼるな　文字ばかりで読む気になれない　またさぼった」と叱責された（10/8 にも同じ叱責）。
    答えは「抄紙日報の見本 4・7・8・11枚目の読み方」と同じ形のスライド（setsumei-shiryo）で作る"""
    m = __import__("re").search(r"^\s*お尋ね\s*[：:](.*)$", inv or "", __import__("re").M)
    ask = m.group(1) if m else ""
    if not (FIG_WORD.search(ask) and HOW_WORD.search(ask)):
        return False
    print("NG：お尋ねが資料の図・数字の意味・読み方・求め方なので、文字のレポートでは答えない。")
    print("  setsumei-shiryo の手順で「読み方」のスライドを作って答える（見本＝production/やりとり/2026-10-17_抄紙日報の見本_4・7・8・11枚目の読み方.md）：")
    print("  1ページ目＝お尋ねごとの答えの表／次から＝実際の1件の例を図に置き、式の箱で計算を見せる／巻末＝用語")
    print("  資料の先頭に <!-- 元の資料：<尋ねられた資料の md> --> を書く（既にある資料へのお尋ね＝クオリティ診断なし・元のクオリティのまま）")
    return True


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
〔0〕専務のお尋ねに答え切っていない＝お尋ねの一部に答えていない、または専務が次に聞き直すことになる中身を残している。また、返答の最初の文が、書き手の「答えの中身」の「お尋ね：」の行への答えになっていない（お尋ねに使われた言葉や分け方で答えず、書き手が調べた事柄から書き始めている）ときも挙げる（お尋ねが示されたときだけ見る。「物差し」は 0）
〔1〕何を言いたいのかが伝わらない文
〔2〕中身を言わずに言い回しだけで済ませた文＝何と何を比べるのか・誰が何をするのか・何を指すのかが、前後の文を読んでも分からない文
〔3〕報告書として不適切な表現：書き手の作業日誌（何を読んだ・どのファイルを直した・プログラムを流した など）／書き手が独自に付けた呼び名／口語・くだけた言い方・感情的な言い方（「〜っぽい」「ざっくり」「とりあえず」「ちゃんと」「黙って」など）／プログラム名・ファイル名が文の主語
〔4〕裏付けの無い断定：書き手の「答えの中身」の「根拠」で推測（未確認）とした事柄を、本文が確かなこととして言い切っている文（本文に「未確認」「推測」などと断っていれば挙げない。「根拠」が示されたときだけ見る）

挙げない文：
- 業務の物の名前（製品名 100S・130S、帳票名、日報アプリ、確認画面、切り抜き、品種名、一覧エクセル など）、人や会社の名前、数字は、そのままで分かる言葉として扱う
- 「アプリは〜と答えます」「アプリがお尋ねします」のように、アプリや機械が主語の文は問題にしない（不適切なのはプログラムのファイル名が主語の文）
- 前後の文や表の見出しを読めば中身が分かる文は挙げない
- 迷う文は挙げない。はっきり伝わらない文だけを挙げる
- 下に示す「社内で通じる言葉」は、専務がふだん使う言葉として扱い、独自の呼び名として挙げない
- レポートへのリンク（[題名] の形）がある返答は、詳しい中身はリンク先のレポートにある前提で読む。結論と伺いが分かれば、中身を全部書けとは言わない。リンクの題名は見出しなので、文になっていなくても挙げない

見本（専務が「分からない」と言った文＝挙げる）：
- 「2で区切れないときは、品種ごとの合計のうち計にいちばん近い品種と比べ、その品種の行を聞く」（何と何を比べるのかが分からない）
- 「品種名に頼らない」（何をするのかが分からない）
- 「質問への Gemini の答えでも、品種名が他と違う行があれば必ず書かせる」（誰に何を書かせるのかが分からない）
- 「品種が2つなのに計が1つなので、85,000m を勤全体の計と判断した」（なぜそうなるのかの筋が通らない）
- 「タスクバーの今の Claude から開くと取り込まれないのが弱点」（「今の Claude」が何を指すのか書いていない＝2026-10-17）
見本（専務が「この日本語が正しい」と言った文＝挙げない）：
- 「確認画面で専務がアプリに質問したとき、品種名がほかの行と違う行があれば、アプリは『1本目だけ角130Sと読んでいます』のように、その行を名指しして答える」
- 「これまで確定した日報に無い品種名を読んだときは、確認画面にその行の紙の切り抜きを出し、『初めて出てきた品種名です。紙に書かれた品種名を入れてください』とお尋ねする」

答えは次の JSON だけを返してください（説明の文は付けない）：
{{"問題": [{{"文": "下書きの文をそのまま", "物差し": "0|1|2|3|4", "理由": "なぜ伝わらないか（短く）"}}]}}
問題が無ければ {{"問題": []}}

{extra}
下書き：
{draft}
"""

PLAIN_CACHE = Path.home() / ".claude" / "state" / "plain-check"


COMPANY = Path(__file__).with_name("company_words.txt")
LAST_PROMPT = Path.home() / ".claude" / "state" / "last_prompt.txt"


def _lines_of(path):
    try:
        return [w.strip() for w in path.read_text(encoding="utf-8").splitlines()
                if w.strip() and not w.lstrip().startswith("#")]
    except Exception:
        return []


def plain_issues(msg, inventory="", check_answer=True):
    """お尋ねに答え切っているか（〔0〕）と、分かる日本語か（〔1〕〜〔3〕）を、別の Claude に1回で点検させる。
    2026-10-05 専務承認：この点検は最後にかける（中身・出し方が決まったあと）。社内で通じる言葉は不合格にしない。
    別の AI に読ませるのは、書き手は前後の事情を知っているため自分の文を「分かる」と読んでしまうから。
    返り値＝(問題の一覧, 点検できなかった理由)。同じ下書きは控えから答える（点検に 20〜40 秒かかるため）"""
    import hashlib, json, re, shutil, subprocess
    text = re.sub(r"\[([^\]]*)\]\((https?://[^)]*)\)", r"[\1]", msg)      # リンクは題名だけを読ませる
    text = re.sub(r"https?://\S+", "", text).strip()
    if not text:
        return [], ""
    extra = "社内で通じる言葉：" + "／".join(_lines_of(COMPANY)) + "\n"
    q = LAST_PROMPT.read_text(encoding="utf-8").strip() if (check_answer and LAST_PROMPT.exists()) else ""
    if q:
        extra += "専務のお尋ね：" + q[:1500] + "\n"
    if inventory:
        extra += "書き手が決めた答えの中身（返答はこれを伝えているか）：\n" + inventory[:1500] + "\n"
    h = hashlib.sha256((extra + text).encode("utf-8")).hexdigest()[:20]
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
        r = subprocess.run([exe, "-p", *lean, "--output-format", "json"],
                           input=PLAIN_PROMPT.format(draft=text, extra=extra),
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


def note_plain_failed(why):
    """★2026-10-22 専務承認（控え帳2の直し方4）：点検のAIが動かなかったことを、次の指示のときに私に届く記録へ書く。
    10/21 は Windows でログインが切れたまま、注意を出して通すだけだったため、丸1日気づかなかった"""
    import datetime
    pending = Path(os.environ.get("HTML_GATE_STATE_DIR") or Path.home() / ".claude/state") / "html-gate_pending.log"
    rec = "\t".join([datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                     f"点検のAIが動かなかった（{why[:60]}）。ログイン切れなら Bash で claude auth status を確かめ、専務に入り直しを伺う",
                     ""]) + "\n"
    try:
        pending.parent.mkdir(parents=True, exist_ok=True)
        old = pending.read_text(encoding="utf-8") if pending.exists() else ""
        if "点検のAIが動かなかった" not in old:   # 同じ知らせは1件だけ（下書きを測るたびに重ねない）
            with open(pending, "a", encoding="utf-8") as f:
                f.write(rec)
    except Exception:
        pass


def stop_on_plain(msg, inventory="", check_answer=True):
    """答え切っていない・伝わらない文が1つでもあれば NG。点検できないときは知らせて通す"""
    issues, why = plain_issues(msg, inventory, check_answer)
    if why:
        print(f"注意：分かる日本語の点検ができませんでした（{why}）。出す前に、専務の立場で1文ずつ読み直すこと")
        note_plain_failed(why)
        return False
    if not issues:
        return False
    print("NG：お尋ねに答え切っていない、または専務に伝わらない文がある。")
    print("    〔0〕は足りない中身を足す（足して基準を超えたらレポートにする）。〔1〕〜〔3〕は言い方だけ直す（中身は減らさない）。")
    print("    〔4〕は確かめてから書くか、本文に「未確認」と書く：")
    for it in issues[:10]:
        print(f"  〔{it.get('物差し', '')}〕「{str(it.get('文', ''))[:70]}」")
        print(f"      → {it.get('理由', '')}")
    return True


INV_RE = __import__("re").compile(r"<!--\s*中身(.*?)-->", __import__("re").S)


def split_inventory(path):
    """下書きから答えの中身の書き出し（<!-- 中身 … -->）を取り出し、(書き出し, 返答の本文) を返す。
    2026-10-05 専務承認：中身を先に決めてから字数を測る順番を、書き出しの有無で機械に確かめさせる"""
    raw = Path(path).read_text(encoding="utf-8")
    m = INV_RE.search(raw)
    if not m:
        return None, raw
    body = (raw[:m.start()] + raw[m.end():]).strip() + "\n"
    return m.group(1).strip(), body


def body_file(path, body):
    """書き出しを除いた返答の本文を、隣のファイルに書いて返す（測る・指紋を残す・レポートにする対象）"""
    out = Path(path).with_name(Path(path).stem + "_返答.md")
    out.write_text(body, encoding="utf-8")
    return str(out)


if __name__ == "__main__":
    # ★2026-10-05 専務承認：確認の順番＝①中身の書き出し → ②字数でチャットかレポートか → ③④別のAIが
    #   「お尋ねに答え切っているか」「分かる日本語か」を1回で点検。9/28 の「削ったら止める」確認は外した
    #   （中身を削っていないかは ①の書き出しと ③で確かめる）。
    if len(sys.argv) < 2:
        sys.exit(main())
    rep = len(sys.argv) >= 3 and sys.argv[1] == "--report"
    src = sys.argv[2] if rep else sys.argv[1]
    inv, body = split_inventory(src)
    if inv is None:                                       # ①
        print("NG：下書きの先頭に、答えの中身の書き出しが無い。次の形で書いてから、もう一度測る（書き出しは返答に含めない）：")
        print("  <!-- 中身\n  お尋ね：\n  結論：\n  理由：\n  数字：\n  選択肢：\n  根拠：\n  次の一手：\n  -->")
        sys.exit(1)
    if stop_on_no_ask(inv):                               # ①' お尋ねの欄（2026-10-21 専務承認）
        sys.exit(1)
    if stop_on_no_basis(inv):                             # ①'' 根拠の欄（2026-10-17 専務承認）
        sys.exit(1)
    path = body_file(src, body)
    if rep:
        # 置き場の指定は、文章の点検（時間がかかる）より先に確かめる（2026-10-13）
        if (sys.argv[4] if len(sys.argv) >= 5 else None) not in PLACES:
            print("NG：レポートの置き場が指定されていない（または一覧に無い）。")
            print(PLACE_HELP)
            sys.exit(1)
        if stop_on_figure_question(inv):                  # 図・数字の意味のお尋ねは図のスライドで答える（2026-10-23 専務承認）
            sys.exit(1)
        # 案ごとの5つの見出しは AI を使わずに数える（待ち時間なし・2026-10-17 専務承認）。
        # レポート全体の「お尋ねに答え切っているか」の AI の点検は、待ち時間が増えるため加えない（同日 専務指示）
        if (stop_on_prose(body) or stop_on_thin_options(body) or stop_on_jargon(path)
                or stop_on_plain(body, inv, check_answer=False)):
            sys.exit(1)
        sys.exit(to_report(path, sys.argv[3] if len(sys.argv) >= 4 else "回答",
                           sys.argv[4] if len(sys.argv) >= 5 else None))
    sys.argv[1] = path
    rc = main()                                           # ②
    if rc != 0:
        sys.exit(rc)
    if stop_on_jargon(path):
        sys.exit(1)
    bad = dead_links(body)
    if bad:   # 開けないリンクを開けるかのように出さない
        print("NG：開けないリンクがある。リンク先を直して（合格印・置き場・配信）から出す：")
        for u, why in bad:
            print(f"  {u}")
            print(f"    → {why}")
        sys.exit(1)
    if stop_on_plain(body, inv):                          # ③④
        sys.exit(1)
    record_ok(path)
    print("合格：返答として出すのは、書き出しを除いた本文（" + path + "）を一字も変えずに")
    sys.exit(0)
