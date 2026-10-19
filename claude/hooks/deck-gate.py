# -*- coding: utf-8 -*-
"""説明資料の書き込みの前の確認（PreToolUse・2026-10-19 専務承認）。

何のためか：
  説明資料（スライド形式）を一発目から見本（抄紙日報の評価と要因）の水準で作るため、
  作り始める前の手順を機械で守らせる（正典＝mino-sakura-hq の docs/説明資料の物差し.md）。
  10/19 の塩化アルミの説明資料は見本も物差しも読まずに作り、4回やり直して約6時間40分かかった。

止める条件（説明資料の書き込みのとき）：
  1. この会話で見本（2026-10-17_抄紙日報の評価と要因_説明資料_見本.md）を読んでいない
  2. この会話で説明資料の手順書（setsumei-shiryo スキル）を使っていない
  3. 新しく作るとき：私が「事前の見立て」をお出ししたあとに、専務の了承の言葉が無い
     （了承・承認・進めて・お願いします・OK など。既にある説明資料の手直しは 1・2 だけを見る）
対象：
  - Edit / Write / MultiEdit で、名前に「説明資料」を含みスライドの形（<section）の md
    （日付が 2026-10-20 より前の資料＝承認の日より前にお出しした物は対象外）
  - Bash で、中身に「説明資料」と「<section」を含む python のプログラムを動かす（資料を作るプログラム）
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
EXEMPT_PY = ("check_deck.py", "report_html.py", "precheck-answer.py", "check_links.py", "check_commit.py", "deck-gate.py")

APPROVE = re.compile(r"了承|承認(する|します|です|だ|で(いい|よい|良い|OK|ok)|。|！|!|\s|$)|^\s*承認|進めて|進めろ|それでやって"
                     r"|お願いします|作って|(?<![A-Za-zＡ-Ｚａ-ｚ])(?:ok|OK|Ok|ｏｋ|ＯＫ|Ｏｋ)(?![A-Za-zＡ-Ｚａ-ｚ])")
NOT_APPROVE = re.compile(r"承認を得|承認な[しく]|承認して(から|い?ない)|無承認|承認が(ない|無い)|承認しない|了承しない|了承できない|了承でき(ず|ません)")


def norm(p):
    return (p or "").replace("\\", "/")


def is_deck_name(path):
    name = os.path.basename(norm(path))
    if "説明資料" not in name or not name.endswith(".md"):
        return False
    m = re.match(r"(\d{4}-\d{2}-\d{2})_", name)
    return not (m and m.group(1) < START)


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


def target(tool, inp, cwd):
    """対象なら (説明, 新しく作るか) を返す。対象外なら None"""
    if tool in ("Edit", "Write", "MultiEdit"):
        p = inp.get("file_path") or ""
        if not is_deck_name(p):
            return None
        exists = os.path.isfile(p)
        body = (inp.get("content") or "") + (inp.get("new_string") or "") + "".join(
            e.get("new_string", "") for e in inp.get("edits") or [] if isinstance(e, dict))
        if "<section" not in body and "<section" not in (read(p) if exists else ""):
            return None
        return (f"{os.path.basename(norm(p))} の書き込み", not exists)
    if tool == "Bash":
        cmd = norm(inp.get("command", ""))
        for w in re.findall(r"[^\s\"'<>|;&]+\.py", cmd):
            if os.path.basename(w) in EXEMPT_PY:
                continue
            src = read(full(w, cwd))
            if "説明資料" in src and "<section" in src:
                return (f"説明資料を作るプログラム {os.path.basename(w)} の実行", False)
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


def agreed_after_plan(evs):
    """私が「事前の見立て」をお出ししたあとに、専務の了承の言葉があるか"""
    last = -1
    for i, e in enumerate(evs):
        if e.get("type") == "assistant" and any(
                b.get("type") == "text" and "事前の見立て" in b.get("text", "") for b in blocks(e)):
            last = i
    if last < 0:
        return False
    for e in evs[last + 1:]:
        t = user_text(e)
        if t and APPROVE.search(NOT_APPROVE.sub("", t)):
            return True
    return False


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
    hit = target(data.get("tool_name", ""), data.get("tool_input") or {}, norm(data.get("cwd", "")))
    if not hit:
        return 0
    what, is_new = hit
    evs = events(data.get("transcript_path", ""))
    lack = []
    if not read_sample(evs):
        lack.append("見本（production/やりとり/2026-10-17_抄紙日報の評価と要因_説明資料_見本.md）をこの会話で読んでいない")
    if not used_skill(evs):
        lack.append("説明資料の手順書（setsumei-shiryo スキル）をこの会話で使っていない")
    if is_new and not agreed_after_plan(evs):
        lack.append("「事前の見立て」をお出ししたあとの専務の了承が無い")
    if not lack:
        log(f"通した\t{what}")
        return 0
    log(f"止めた\t{what}\t{'／'.join(lack)}")
    sys.stderr.write(
        f"[説明資料の確認] {what} を止めました。\n"
        + "".join(f"  ・{x}\n" for x in lack)
        + "手順書（setsumei-shiryo）を使い、見本と物差し（docs/説明資料の物差し.md）を読み、"
          "事前の見立てをお出しして了承をいただいてから作ってください。\n")
    return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
