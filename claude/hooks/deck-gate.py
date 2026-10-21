# -*- coding: utf-8 -*-
"""スライド資料・エクセルの書き込みの前の確認＝クオリティ診断（PreToolUse・2026-10-19 承認・2026-10-21 クオリティ診断を足した）。

クオリティ診断（2026-10-21 専務承認）：
  スライド資料・エクセルを新しく作る・直すときは、私が「クオリティ診断」で ①体裁だけ（A）か ②体裁と中身（A＋B）かを伺い、
  専務のお答えがあるまで書き込みを止める。お答えは対象ごとに mino-sakura-hq の .deck_stamps/診断/ に控え、
  採点（tools/check_deck.py）・エクセルの受付・ページ作りがその控えで①か②か・対象かを見分ける。
  妥協の合格印（check_deck.py --accept）は、理由と妥協案のレポートのあとに専務の承認の言葉が無ければ止める。
  エクセルを作るプログラムは、新しく書くときも直すときも対象（定例の作り直し＝プログラムを流すだけは対象外）。


何のためか：
  説明資料（スライド形式）を一発目から見本（抄紙日報の評価と要因）の水準で作るため、
  作り始める前の手順を機械で守らせる（正典＝mino-sakura-hq の docs/説明資料の物差し.md）。
  10/19 の塩化アルミの説明資料は見本も物差しも読まずに作り、4回やり直して約6時間40分かかった。

止める条件（スライド資料の書き込みのとき）：
  0. クオリティ診断（①か②）を伺っていない、または専務のお答えが無い（2026-10-21）
  1. この会話で見本（2026-10-17_抄紙日報の評価と要因_説明資料_見本.md）を読んでいない
  2. この会話で説明資料の手順書（setsumei-shiryo スキル）を使っていない
  3. 新しく作るとき：私が「事前の見立て」をお出ししたあとに、専務の了承の言葉が無い
     （了承・承認・進めて・お願いします・OK など。既にある説明資料の手直しは 1・2 だけを見る）
対象：
  - Edit / Write / MultiEdit で、名前に「説明資料」を含みスライドの形（<section）の md
    （2026-10-21 から日付で外さない＝過去の資料も直すときは対象。名前に「スライド資料」を含む物も対象）
  - Bash で、中身に「説明資料」と「<section」を含む python のプログラムを動かす（資料を作るプログラム）
エクセル（2026-10-20 専務承認・物差しをエクセルへ広げる）：
  - Edit / Write / MultiEdit で、エクセルを作る python のプログラム（中身に openpyxl と .xlsx を含む）を
    新しく書くとき・直すとき（2026-10-21 クオリティ診断で、直すときも対象にした）
  - 止める条件＝上の 0・1・2 に加え、この会話でエクセルの見本（原料仕入分析）の画像を見ていない。新しく書くときは 3 も
  - 定例業務の作り直し（プログラムを流すだけ）は止めない
止めたら exit 2 で理由を私に返し（専務の画面には出ない）、記録（~/.claude/logs/deck-gate.log）に残す。
"""
import datetime as dt
import json
import os
import re
import sys

START = "2026-10-20"
SAMPLE = "抄紙日報の評価と要因_説明資料_見本"
SKILL = "setsumei-shiryo"
# 説明資料を扱う仕組みのプログラム自身は、資料を作るプログラムとして数えない
EXEMPT_PY = ("check_deck.py", "report_html.py", "precheck-answer.py", "check_links.py", "check_commit.py", "deck-gate.py",
             "check_excel.py", "xlsx_opener.py", "excel_style.py", "print_xlsx.py", "analysis_glossary.py")
EXCEL_SAMPLE = "原料仕入分析"   # エクセルの見本（見せ方と体裁）＝この名前の画像（excel_check/原料仕入分析/…jpg）を見たか

APPROVE = re.compile(r"了承|承認(する|します|です|だ|で(いい|よい|良い|OK|ok)|。|！|!|\s|$)|^\s*承認|進めて|進めろ|それでやって"
                     r"|お願いします|作って|(?<![A-Za-zＡ-Ｚａ-ｚ])(?:ok|OK|Ok|ｏｋ|ＯＫ|Ｏｋ)(?![A-Za-zＡ-Ｚａ-ｚ])")
NOT_APPROVE = re.compile(r"承認を得|承認な[しく]|承認して(から|い?ない)|無承認|承認が(ない|無い)|承認しない|了承しない|了承できない|了承でき(ず|ません)")


def norm(p):
    return (p or "").replace("\\", "/")


def is_deck_name(path):
    name = os.path.basename(norm(path))
    if ("説明資料" not in name and "スライド資料" not in name) or not name.endswith(".md"):
        return False
    return True   # 2026-10-21 クオリティ診断：過去の資料も直すときは対象（日付で外さない）


def read(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def full(w, cwd):
    w = norm(os.path.expandvars(w.strip("\"'"))).replace("~", norm(os.path.expanduser("~")))
    if cwd and not re.match(r"^([A-Za-z]:)?/", w):
        w = cwd.rstrip("/") + "/" + w
    return w


def excel_target(tool, inp, cwd):
    """エクセルを作るプログラムの書き込みなら (説明, 新しく作るか, "excel")"""
    p = inp.get("file_path") or ""
    if tool not in ("Edit", "Write", "MultiEdit") or not p.endswith(".py") or os.path.basename(p) in EXEMPT_PY:
        return None
    exists = os.path.isfile(p)
    body = (inp.get("content") or "") + (inp.get("new_string") or "") + "".join(
        e.get("new_string", "") for e in inp.get("edits") or [] if isinstance(e, dict))
    src = body + (read(p) if exists else "")
    if "openpyxl" not in src or ".xlsx" not in src:
        return None
    root = repo_root(os.path.dirname(norm(p)) or cwd)   # クオリティ診断を持つリポジトリ（mino-sakura-hq）のプログラムだけ
    if not root or not os.path.isfile(root + "/tools/check_deck.py"):
        return None
    return (f"エクセルを作るプログラム {os.path.basename(norm(p))} の書き込み", not exists, "excel")


def target(tool, inp, cwd):
    """対象なら (説明, 新しく作るか, 種類) を返す。対象外なら None"""
    if tool in ("Edit", "Write", "MultiEdit"):
        p = inp.get("file_path") or ""
        if not is_deck_name(p):
            return excel_target(tool, inp, cwd)
        exists = os.path.isfile(p)
        body = (inp.get("content") or "") + (inp.get("new_string") or "") + "".join(
            e.get("new_string", "") for e in inp.get("edits") or [] if isinstance(e, dict))
        if "<section" not in body and "<section" not in (read(p) if exists else ""):
            return None
        return (f"{os.path.basename(norm(p))} の書き込み", not exists, "deck")
    if tool == "Bash":
        cmd = norm(inp.get("command", ""))
        for w in re.findall(r"[^\s\"'<>|;&]+\.py", cmd):
            if os.path.basename(w) in EXEMPT_PY:
                continue
            src = read(full(w, cwd))
            if ("説明資料" in src or "スライド資料" in src) and "<section" in src:
                return (f"スライド資料を作るプログラム {os.path.basename(w)} の実行", False, "deck")
    return None


def events(transcript):
    out = []
    try:
        lines = open(transcript, encoding="utf-8").read().splitlines()
    except Exception:
        return out
    for line in lines:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def blocks(e):
    c = (e.get("message") or {}).get("content")
    if isinstance(c, str):
        return [{"type": "text", "text": c}]
    return [b for b in c or [] if isinstance(b, dict)]


def read_sample(evs):
    """この会話で見本を読んだか（Read か、見本の名前を含む Bash）"""
    for e in evs:
        if e.get("type") != "assistant":
            continue
        for b in blocks(e):
            if b.get("type") != "tool_use":
                continue
            inp = b.get("input") or {}
            if b.get("name") == "Read" and SAMPLE in norm(inp.get("file_path", "")):
                return True
            if b.get("name") == "Bash" and SAMPLE in inp.get("command", ""):
                return True
    return False


def saw_excel_sample(evs):
    """この会話でエクセルの見本（原料仕入分析）の画像を開いたか"""
    for e in evs:
        if e.get("type") != "assistant":
            continue
        for b in blocks(e):
            if b.get("type") == "tool_use" and b.get("name") == "Read":
                f = norm((b.get("input") or {}).get("file_path", ""))
                if EXCEL_SAMPLE in f and f.lower().endswith((".jpg", ".png")):
                    return True
    return False


def used_skill(evs):
    for e in evs:
        if e.get("type") != "assistant":
            continue
        for b in blocks(e):
            if b.get("type") == "tool_use" and b.get("name") == "Skill" and SKILL in str((b.get("input") or {}).get("skill", "")):
                return True
    return False


def user_text(e):
    """専務のご発言（ツールの結果や仕組みの差し込みは除く）。違えば None"""
    if e.get("type") != "user" or e.get("isMeta"):
        return None
    bs = blocks(e)
    if any(b.get("type") == "tool_result" for b in bs):
        return None
    t = "".join(b.get("text", "") for b in bs if b.get("type") == "text")
    return t or None


def repo_root(start):
    """そのファイル（またはフォルダ）が入っているリポジトリの一番上（.git のある所）。無ければ "" """
    d = norm(start)
    for _ in range(12):
        if d and os.path.isdir(d.rstrip("/") + "/.git"):
            return d.rstrip("/")
        nd = os.path.dirname(d.rstrip("/"))
        if not nd or nd == d:
            break
        d = nd
    return ""


def rel_in(root, path):
    p = norm(path)
    return p[len(root) + 1:] if root and p.startswith(root + "/") else p


def excel_names(src):
    """作るプログラムに書かれたエクセルの名前（{…} は * に置き換える）＝受付がそのエクセルを対象と見分けるために控える"""
    out = []
    for m in re.findall(r"[\"']([^\"'\n]*?\.xlsx)[\"']", src):
        n = re.sub(r"\{[^}]*\}", "*", os.path.basename(norm(m)))
        if n and n != ".xlsx" and n not in out:
            out.append(n)
    return out


def deck_md_in(src):
    """スライド資料を作るプログラムに書かれた md の相対パス（最初の1つ）"""
    found = [norm(m) for m in re.findall(r"[\"']([^\"'\n]*(?:説明資料|スライド資料)[^\"'\n]*\.md)[\"']", src)
             if "見本" not in m]   # 見た目の決まりを読む見本は除く（書き出す先の md を選ぶ）
    return found[0] if found else ""


def diagnosis(evs):
    """私が「クオリティ診断」を伺ったあとの、専務の ①② のお答え。(①|②|"", 専務の言葉)"""
    last = -1
    for i, e in enumerate(evs):
        if e.get("type") == "assistant" and any(
                b.get("type") == "text" and "クオリティ診断" in b.get("text", "") for b in blocks(e)):
            last = i
    if last < 0:
        return "", ""
    for e in evs[last + 1:]:
        t = user_text(e)
        if not t:
            continue
        hits = [(t.find(k), v) for k, v in (("①", "①"), ("体裁だけ", "①"), ("②", "②"), ("体裁と中身", "②"),
                                            ("A＋B", "②"), ("A+B", "②")) if k in t]
        if hits:
            return min(hits)[1], t.strip()[:80]
    return "", ""


def save_record(root, key, kind, mode, said, src):
    """クオリティ診断の控え（mino-sakura-hq の .deck_stamps/診断/）。同じ診断なら不合格の回数を引き継ぐ"""
    if not root or not os.path.isfile(root + "/tools/check_deck.py"):
        return
    d = root + "/.deck_stamps/診断"
    os.makedirs(d, exist_ok=True)
    f = d + "/" + key.replace("/", "__") + ".json"
    old = {}
    try:
        old = json.loads(read(f) or "{}")
    except ValueError:
        pass
    rec = {"対象": key, "種類": kind, "診断": mode, "専務のお答え": said,
           "日時": f"{dt.datetime.now():%Y-%m-%d %H:%M}",
           "不合格の回数": old.get("不合格の回数", 0) if old.get("診断") == mode else 0}
    if kind == "excel":
        rec["名前"] = sorted(set(old.get("名前", [])) | set(excel_names(src)))
        rec["エクセル"] = old.get("エクセル", [])
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")


def agreed_after(evs, word):
    """私が word を含む文をお出ししたあとに、専務の承認の言葉があるか"""
    last = -1
    for i, e in enumerate(evs):
        if e.get("type") == "assistant" and any(
                b.get("type") == "text" and word in b.get("text", "") for b in blocks(e)):
            last = i
    if last < 0:
        return False
    for e in evs[last + 1:]:
        t = user_text(e)
        if t and APPROVE.search(NOT_APPROVE.sub("", t)):
            return True
    return False


def agreed_after_plan(evs):
    """私が「事前の見立て」をお出ししたあとに、専務の了承の言葉があるか"""
    return agreed_after(evs, "事前の見立て")


def log(msg):
    try:
        d = os.path.join(os.path.expanduser("~"), ".claude", "logs")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "deck-gate.log"), "a", encoding="utf-8") as f:
            f.write(f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}\t{msg}\n")
    except Exception:
        pass


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    tool, inp, cwd = data.get("tool_name", ""), data.get("tool_input") or {}, norm(data.get("cwd", ""))
    evs = None
    # 妥協の合格印は、理由と妥協案のレポートをお出ししたあとの専務の承認の言葉が無ければ止める
    if tool == "Bash" and re.search(r"python3?(\.exe)?\s+\S*check_deck\.py\s+--accept\b", inp.get("command", "")):
        evs = events(data.get("transcript_path", ""))
        if not agreed_after(evs, "妥協"):
            log("止めた\t妥協の合格印\t専務の承認が無い")
            sys.stderr.write("[クオリティ診断] 妥協の合格印を止めました。理由と妥協案のレポートをお出しし、"
                             "専務の承認の言葉をいただいてから付けてください。\n")
            return 2
        log("通した\t妥協の合格印")
        return 0
    hit = target(tool, inp, cwd)
    if not hit:
        return 0
    what, is_new, kind = hit
    evs = evs or events(data.get("transcript_path", ""))
    lack = []
    mode, said = diagnosis(evs)
    if not mode:
        lack.append("クオリティ診断（①体裁だけ＝A／②体裁と中身＝A＋B）を専務に伺っていない、またはお答えが無い")
    if not read_sample(evs):
        lack.append("見本（production/やりとり/2026-10-17_抄紙日報の評価と要因_説明資料_見本.md）をこの会話で読んでいない")
    if kind == "excel" and not saw_excel_sample(evs):
        lack.append("エクセルの見本（原料仕入分析）の画像をこの会話で見ていない（tools/check_excel.py で書き出した excel_check/原料仕入分析/ の画像）")
    if not used_skill(evs):
        lack.append("スライド資料・エクセルの手順書（setsumei-shiryo スキル）をこの会話で使っていない")
    if is_new and not agreed_after_plan(evs):
        lack.append("「事前の見立て」をお出ししたあとの専務の了承が無い")
    if not lack:
        # 診断の控えを付ける（採点・受付・ページ作りがこれで①か②かと対象かを見分ける）
        try:
            if tool == "Bash":
                cmd = norm(inp.get("command", ""))
                prog = next((full(w, cwd) for w in re.findall(r"[^\s\"'<>|;&]+\.py", cmd)
                             if os.path.basename(w) not in EXEMPT_PY), "")
                root = repo_root(os.path.dirname(prog) or cwd)
                md = deck_md_in(read(prog))
                if md:
                    save_record(root, rel_in(root, md if re.match(r"^([A-Za-z]:)?/", md) else root + "/" + md), "deck", mode, said, "")
            else:
                p = full(inp.get("file_path", ""), cwd)
                root = repo_root(os.path.dirname(p))
                src = (inp.get("content") or "") + (inp.get("new_string") or "") + read(p)
                save_record(root, rel_in(root, p), kind, mode, said, src)
        except Exception as ex:
            log(f"控えを付けられなかった\t{what}\t{type(ex).__name__}")
        log(f"通した\t{what}\t診断{mode}")
        return 0
    log(f"止めた\t{what}\t{'／'.join(lack)}")
    sys.stderr.write(
        f"[クオリティ診断] {what} を止めました。\n"
        + "".join(f"  ・{x}\n" for x in lack)
        + "手順書（setsumei-shiryo）を使い、クオリティ診断で①か②を専務に伺い、見本と物差し（docs/説明資料の物差し.md）を読み、"
          "新しく作るときは事前の見立てをお出しして了承をいただいてから作ってください。\n")
    return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
