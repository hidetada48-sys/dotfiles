# -*- coding: utf-8 -*-
"""エクセルを開く前の点検（PreToolUse / Bash）。2026-09-18 専務指示・2026-10-21 クオリティ診断に改めた。

Claude がエクセルを開くコマンド（start / xdg-open / Invoke-Item / explorer）を出したら、
エクセルの受付（tools/xlsx_opener.py の openable）と同じ判定で、開いてよいかを見る。
- クオリティ診断（①か②）を伺って作った・直したエクセルで、合格前の物 → 開かせない（exit 2）
- 定例の作り直し・過去の分析・原本は止めない（9/18 の「今日作った物は体裁検査の合格印が要る」はやめた）
- tools/xlsx_opener.py を持たないリポジトリのエクセルは対象外
正典：mino-sakura-hq docs/plans/2026-10-21-クオリティ診断の作り方（案）.md
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
        # 受付を持つリポジトリか（親をたどって tools/xlsx_opener.py を探す）
        repo = next((d for d in [p.parent, *p.parents] if (d / "tools" / "xlsx_opener.py").exists()), None)
        if repo is None:
            continue
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("xlsx_opener", repo / "tools" / "xlsx_opener.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            code, _, msg, _ = mod.openable(os.path.relpath(p, repo).replace("\\", "/"))
        except Exception:
            continue   # 判定のプログラムが読めないときは止めない
        if code != 200:
            bad.append(f"{msg}（python tools/check_deck.py で採点する）")
    if bad:
        sys.stderr.write(
            "[クオリティ診断] このエクセルは合格前のため開けません。\n  "
            + "\n  ".join(bad) + "\n"
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
