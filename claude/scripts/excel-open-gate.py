# -*- coding: utf-8 -*-
"""エクセルを開く前の関門（PreToolUse / Bash）。2026-09-18 専務指示「機械的に必ず守られるルールに」。

Claude がエクセルを開くコマンド（start / xdg-open / Invoke-Item / explorer）を出したら、
そのエクセルに「合格印」があるかを見る。合格印＝ tools/check_excel.py が
〔中身の検査に合格〕かつ〔見た目の書き出しまで済んだ〕ときにだけ、その版（更新時刻・大きさ）で残す印。
- 印が無い／エクセルが印の後に作り直された → 開かせない（exit 2）。検査を走らせるよう指示する
- 対象は「今日作った・更新したエクセル」だけ（既存の古いエクセルは次に作り直すときに移す）
- check_excel.py を持たないリポジトリのエクセルは対象外
正典：mino-sakura-hq CLAUDE.md「エクセル成果物の体裁」／lib/excel_style.py
"""
import datetime as dt
import json
import os
import re
import shlex
import sys
import tempfile
from pathlib import Path

# 実際にエクセルを開くコマンドの形だけ（2026-09-18：Pythonの open( に反応して誤って止めたため絞った）
OPEN_WORDS = re.compile(r"(cmd(\.exe)?\s+/+c\s+start\b|\bstart\s+\"\"|xdg-open\s|Invoke-Item\s|explorer(\.exe)?\s)", re.I)


def xlsx_paths(cmd):
    """コマンド文字列からエクセルのパスを取り出す（引用符あり・なし両方）"""
    found = re.findall(r'"([^"]+\.xlsx)"', cmd) + re.findall(r"'([^']+\.xlsx)'", cmd)
    rest = re.sub(r'"[^"]*"|\'[^\']*\'', " ", cmd)
    found += re.findall(r"(\S+\.xlsx)\b", rest)
    return found


def main():
    if os.name != "nt":
        return 0   # 関門はWindowsだけ。Linuxでは止めない（専務指示 2026-09-19）
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))   # 日本語パスを文字化けさせない
    except Exception:
        return 0
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if ".xlsx" not in cmd or not OPEN_WORDS.search(cmd):
        return 0
    cwd = Path(data.get("cwd") or os.getcwd())
    bad = []
    for raw in xlsx_paths(cmd):
        p = Path(raw.replace("\\\\", "\\"))
        if not p.is_absolute():
            p = cwd / p
        if not p.exists():
            continue
        # 検査ツールを持つリポジトリか（親をたどって tools/check_excel.py を探す）
        repo = next((d for d in [p.parent, *p.parents] if (d / "tools" / "check_excel.py").exists()), None)
        if repo is None:
            continue
        st = p.stat()
        if dt.date.fromtimestamp(st.st_mtime) != dt.date.today():
            continue   # 今日作った・更新したものだけ
        stamp = Path(tempfile.gettempdir()) / "excel_check" / p.stem / "PASS"
        ok = stamp.exists() and stamp.read_text(encoding="utf-8").strip() == f"{st.st_mtime_ns} {st.st_size}"
        if not ok:
            rel = os.path.relpath(p, repo)
            bad.append(f"python tools/check_excel.py \"{rel}\"")
    if bad:
        sys.stderr.write(
            "[エクセル体裁の関門] このエクセルは体裁検査の合格印がありません（未検査、または検査後に作り直した）。\n"
            "開く前に次を実行し、不合格なら lib/excel_style.py に従って直すこと。\n"
            "合格したら、書き出された画像（全シート・全グラフ）をすべて開いて目で確かめてから開くこと。\n  "
            + "\n  ".join(bad) + "\n"
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
