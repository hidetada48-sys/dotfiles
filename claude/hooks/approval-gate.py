# -*- coding: utf-8 -*-
"""承認の無い書き換えを止める関門（PreToolUse・2026-10-05 専務承認）。

何のためか：
  専務の決まり「変更前に何をするか説明し、承認を得てから実行する」を、私（Claude）が何度も破った
  （2026-10-05 朝、「直してくれ」を承認と取り違え、日報アプリを書き換えてサーバーへ置いた）。
  そこで、仕組みのファイルの書き換えと日報アプリの組み立て・配置を、専務の直前のご発言に
  承認の言葉が無いかぎり機械で止める。

止めるもの：
  - Edit / Write / NotebookEdit で、仕組みのファイル（PROTECTED）を書き換える
  - Bash で、日報アプリの組み立て・配置（PyInstaller・deploy.py）を行う
  - Bash で、仕組みのファイルの場所を含み、かつ書き込み・消去・差し戻しの操作をする
止めないもの：
  定例業務で作るもの（残作業一覧・レポート・データ・案件台帳・記録）、記憶、読む・調べる・測る作業、一時的な下書き
承認とみなす言葉（専務の直前のご発言1つだけを見る＝次のご発言で切れる）：
  「承認」（「承認を得て」「承認なし」などの言い回しは除く）「進めて」「それでやって」「お願いします」「ok」（2026-10-06 追加）
  「直してくれ」「〜しろ」「やってくれ」だけの依頼は承認とみなさない
止めたら exit 2 で理由を私に返し、記録（~/.claude/logs/approval-gate.log）に残す。
"""
import datetime as dt
import json
import os
import re
import sys

HOME = os.path.expanduser("~").replace("\\", "/")

# 仕組みのファイル（パスに含まれていれば対象）。区切りは / にそろえて比べる
PROTECTED = [
    "mino-sakura-hq/apps/", "mino-sakura-hq/tools/", "mino-sakura-hq/lib/", "mino-sakura-hq/.claude/",
    "mino-sakura-hq/CLAUDE.md",
    "/dotfiles/",                                  # ~/.claude/hooks・scripts・settings.json・CLAUDE.md の実体
    "/.claude/hooks/", "/.claude/scripts/", "/.claude/settings", "/.claude/CLAUDE.md", "/.claude/skills/",
]
PROTECTED_RE = [re.compile(r"mino-sakura-hq/[^/]+/scripts/")]   # 各参謀の scripts（sales/scripts など）
# 対象から外すもの（記憶・下書き）
EXEMPT = ["/.claude/projects/", "/AppData/Local/Temp/", "/scratchpad/"]

# Bash で必ず止める操作（日報アプリの組み立て・配置）
ALWAYS_BASH = re.compile(r"PyInstaller|deploy\.py", re.I)
# Bash の書き込み・消去・差し戻しの操作
WRITE_BASH = re.compile(r"(^|[\s;&|(])(tee|sed\s+-i|cp|mv|rm|rmdir|del|copy|move|mkdir|touch|truncate|ln|"
                        r"git\s+(checkout|restore|reset|apply|stash|mv|rm)|Set-Content|Out-File|Remove-Item|Copy-Item|Move-Item)\b", re.I)
# リダイレクト（> や >>）の書き込み先
REDIRECT = re.compile(r"\d?>>?\s*([^\s;&|<>]+)")

APPROVE = re.compile(r"承認(する|します|です|だ|で(いい|よい|良い|OK|ok)|。|！|!|\s|$)|^\s*承認|進めて|それでやって|お願いします"
                     r"|(?<![A-Za-zＡ-Ｚａ-ｚ])(?:ok|OK|Ok|ｏｋ|ＯＫ|Ｏｋ)(?![A-Za-zＡ-Ｚａ-ｚ])")   # 「ok」も承認（2026-10-06 専務指示）
NOT_APPROVE = re.compile(r"承認を得|承認な[しく]|承認して(から|い?ない)|無承認|承認が(ない|無い)|承認しない")


def norm(p):
    return (p or "").replace("\\", "/")


def protected(path):
    p = norm(path)
    if any(e in p for e in EXEMPT):
        return False
    return any(k in p for k in PROTECTED) or any(r.search(p) for r in PROTECTED_RE)


def last_user_text(transcript):
    """専務の直前のご発言（ツールの結果や仕組みの差し込みは除く）"""
    try:
        lines = open(transcript, encoding="utf-8").read().splitlines()
    except Exception:
        return None
    for line in reversed(lines):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("type") != "user" or e.get("isMeta"):
            continue
        c = (e.get("message") or {}).get("content")
        if isinstance(c, str):
            return c
        if isinstance(c, list):
            if any(b.get("type") == "tool_result" for b in c if isinstance(b, dict)):
                continue
            t = "".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
            if t:
                return t
    return None


def approved(text):
    if not text:
        return False
    # 否定の言い回しを消してから、承認の言葉を探す
    return bool(APPROVE.search(NOT_APPROVE.sub("", text)))


def full(w, cwd):
    """相対パスは作業フォルダからの位置にする（~ はホームに置き換える）"""
    # $TEMP などの置き場の名前は実際のフォルダの場所に置き換える（2026-10-05：日報アプリのフォルダで
    # 「$TEMP/sim.py」への書き込みを、日報アプリのファイルの書き換えと取り違えた）
    w = norm(os.path.expandvars(w.strip("\"'"))).replace("~", HOME)
    if cwd and not re.match(r"^([A-Za-z]:)?/", w):
        w = cwd.rstrip("/") + "/" + w
    return w


def target(tool, inp, cwd=""):
    """止める対象なら、何をしようとしているかの説明を返す（対象外なら空）"""
    if tool in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
        p = inp.get("file_path") or inp.get("notebook_path") or ""
        return f"{p} の書き換え" if protected(p) else ""
    if tool == "Bash":
        cmd = norm(inp.get("command", ""))
        if ALWAYS_BASH.search(cmd):
            return "日報アプリの組み立て・サーバーへの配置"
        for dst in REDIRECT.findall(cmd):
            if protected(full(dst, cwd)):
                return f"{dst} への書き込み（Bash）"
        if WRITE_BASH.search(cmd):
            words = re.findall(r"[^\s\"'<>|;&]+", cmd)
            hit = [w for w in words if not w.startswith("-") and protected(full(w, cwd))]
            if hit:
                hit.sort(key=lambda w: not ("/" in w or "." in w))     # 説明にはファイルらしい語を出す（「sed」などの命令名を出さない）
                return f"{hit[0]} への書き込み・消去・差し戻し（Bash）"
    return ""


def log(msg):
    try:
        d = os.path.join(os.path.expanduser("~"), ".claude", "logs")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "approval-gate.log"), "a", encoding="utf-8") as f:
            f.write(f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}\t{msg}\n")
    except Exception:
        pass


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    what = target(data.get("tool_name", ""), data.get("tool_input") or {}, norm(data.get("cwd", "")))
    if not what:
        return 0
    text = last_user_text(data.get("transcript_path", ""))
    if approved(text):
        log(f"通した\t{what}")
        return 0
    log(f"止めた\t{what}")
    sys.stderr.write(
        f"[承認の関門] {what} は、専務の承認が無いため止めました。\n"
        "何をするか（どのファイルをどう直すか・サーバーへ置くか）を専務に示し、"
        "「承認」「進めて」などのお返事をいただいてから実行してください。"
        "「直してくれ」「〜しろ」などの依頼は承認ではありません。\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
