# -*- coding: utf-8 -*-
"""広く重くて新しい仕組みづくりで brainstorming を使ったかの見張り（PostToolUse・2026-10-12 専務承認）。

何のためか：
  全体の決まり「新機能・スクリプトを作る前は必ず brainstorming スキルを発動する」を、私（Claude）が守っていなかった
  （2026-10-12 専務「お前最近ブレーンストーミング使わないな」）。ただし小さな手直しにまで使う必要はない
  （同日 専務「この程度のことは使わなくていい。広く重くて新しい仕組みづくりは使うことを機械で見張れ」）。

見張る対象（広く重くて新しい仕組み）：
  〔1〕新しいプログラム・スキル・フックのファイルを作ったとき（Write で新しく作成）
  〔2〕1つの会話で、3本以上のプログラムに手を入れたとき（Edit / Write の書き換え）
  対象外＝既存のプログラム1本・2本の手直し
見張り方：
  その会話の記録（transcript）に brainstorming スキルを使った跡が無ければ、
  私にだけその場で知らせ（additionalContext）、次の指示のときの違反の知らせ（html-gate_pending.log）と
  記録（~/.claude/logs/brainstorm-gate.log）に残す。作業は止めない（2026-09-26 専務指示＝関門は止めずに記録するだけ）。
  同じ会話で同じ理由の知らせは1回だけ。
"""
import datetime as dt
import json
import os
import re
import sys

HOME = os.path.expanduser("~").replace("\\", "/")
STATE = os.path.join(HOME, ".claude", "state")
LOG = os.path.join(HOME, ".claude", "logs", "brainstorm-gate.log")
PENDING = os.path.join(STATE, "html-gate_pending.log")

# プログラムの置き場（パスに含まれていれば対象）。区切りは / にそろえて比べる
AREAS = ["mino-sakura-hq/apps/", "mino-sakura-hq/tools/", "mino-sakura-hq/lib/", "mino-sakura-hq/.claude/skills/",
         "/dotfiles/claude/hooks/", "/dotfiles/claude/scripts/", "/dotfiles/claude/skills/",
         "/.claude/hooks/", "/.claude/scripts/", "/.claude/skills/"]
AREAS_RE = [re.compile(r"mino-sakura-hq/[^/]+/scripts/")]      # 各参謀の scripts（production/scripts など）
EXTS = (".py", ".sh", ".ps1", ".js", ".ts", ".bat", ".spec")
MANY = 3                                                       # 〔2〕の本数


def is_program(path):
    p = path.replace("\\", "/")
    if not (any(a in p for a in AREAS) or any(r.search(p) for r in AREAS_RE)):
        return False
    return p.endswith(EXTS) or p.endswith("/SKILL.md")


def brainstormed(transcript):
    """その会話で brainstorming スキルを使ったか"""
    try:
        with open(transcript, encoding="utf-8") as f:
            for line in f:
                if '"Skill"' in line and "brainstorming" in line:
                    return True
    except OSError:
        pass
    return False


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        return
    tool = d.get("tool_name", "")
    if tool not in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
        return
    path = (d.get("tool_input") or {}).get("file_path") or (d.get("tool_input") or {}).get("notebook_path") or ""
    if not path or not is_program(path):
        return
    sid = d.get("session_id", "nosession")
    os.makedirs(STATE, exist_ok=True)
    sf = os.path.join(STATE, f"brainstorm-gate_{sid}.json")
    try:
        st = json.load(open(sf, encoding="utf-8"))
    except Exception:
        st = {"files": [], "told": []}
    norm = path.replace("\\", "/")
    if norm not in st["files"]:
        st["files"].append(norm)
    resp = d.get("tool_response") or {}
    created = tool == "Write" and isinstance(resp, dict) and resp.get("type") == "create"
    reason = ""
    if created and "new" not in st["told"]:
        reason, key = f"新しいプログラムを作りました（{os.path.basename(norm)}）", "new"
    elif len(st["files"]) >= MANY and "many" not in st["told"]:
        reason, key = f"この会話で {len(st['files'])} 本のプログラムに手を入れました", "many"
    if reason and not brainstormed(d.get("transcript_path", "")):
        st["told"].append(key)
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        msg = (f"[brainstorming の見張り] {reason}が、この会話で brainstorming スキルを使っていません。"
               "広く重くて新しい仕組みづくりは、作る前に brainstorming を使う（2026-10-12 専務指示）。"
               "続ける前に brainstorming スキルを発動し、設計を固めてから進めること。")
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{now}\t{sid}\t{reason}\t{norm}\n")
        with open(PENDING, "a", encoding="utf-8") as f:
            f.write(f"{now}\tbrainstorming を使わずに{reason}\n")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}},
                         ensure_ascii=False))
    json.dump(st, open(sf, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()
