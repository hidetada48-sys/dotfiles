# -*- coding: utf-8 -*-
"""作る前の確認（~/.claude/hooks/deck-gate.py）の承認と診断の判定の試験（2026-11-04 専務承認・控え帳 11/4 夜 案3）。
使い方：python ~/.claude/scripts/test-deck-gate.py（Linux は python3）。全部合格なら 0 で終わる。"""
import importlib.util
import os
import sys

HOOK = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "deck-gate.py")
spec = importlib.util.spec_from_file_location("deck_gate", HOOK)
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)


def A(text):
    """私の発言"""
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def U(text):
    """専務のご発言"""
    return {"type": "user", "message": {"content": text}}


ASK = "この作りで、原料のエクセルを作ってよろしいですか。クオリティ診断は①体裁だけ／②体裁と中身のどちらにしますか。"
cases = [
    # (説明, 会話, 期待する診断, 期待する承認)
    ("伺いに「体裁だけで作れ」", [A(ASK), U("体裁だけで作れ")], "①", True),
    ("伺いに「②で進めて」", [A(ASK), U("②で進めて")], "②", True),
    ("伺いに「作れ」だけ（診断は前に言われた）", [U("クオリティ診断は体裁だけでいいからな"), A(ASK), U("作れ")], "①", True),
    ("伺いに「はい」", [A(ASK), U("体裁だけ。はい")], "①", True),
    ("打ち消し「いや待て」", [A(ASK), U("いや待て")], "", False),
    ("問い返し", [A(ASK), U("体裁だけってなに？")], "①", False),
    ("承認のあと打ち消し", [A(ASK), U("体裁だけで作れ"), A("作ります。"), U("やめろ")], "①", False),
    ("私がもう一度診断と書いても前のお答えを捨てない",
     [A(ASK), U("体裁だけで作れ"), A("クオリティ診断は体裁だけで作ります。")], "①", True),
    ("伺いの前の①は診断にしない", [U("①を直せ"), A("事前の見立てです。")], "", False),
    ("事前の見立てのあと「承認」", [A("事前の見立てをお出しします。この見立てで作ってよろしいですか。"), U("承認")], "", True),
    # 2026-11-09 専務承認（控え帳 11/9 13:41 案2）：診断なしのお答えも作る伺いへの承認。打ち消し・伺いの無い所の診断なしは通さない
    ("伺いに「診断なし」", [A(ASK), U("診断なし")], "なし", True),
    ("診断なしを伺った文のあとの「診断なし」", [A("作ってよろしいですか？"), U("作れ"), A("診断なしで作ってよろしいですか？"), U("診断なし")], "なし", True),
    ("「診断なしはだめだ」は診断なしにしない", [A(ASK), U("いや待て　診断なしはだめだ")], "", False),
    ("伺いの無い所の「診断なし」は承認でない", [A("照合表を作りました。"), U("診断なし")], "なし", False),
]
bad = 0
for name, evs, want_d, want_a in cases:
    d = G.diagnosis(evs)[0]
    a = G.agreed_after_plan(evs)
    ok = d == want_d and a == want_a
    bad += not ok
    print(("合格" if ok else "不合格"), name, f"診断={d or 'なし'}（期待 {want_d or 'なし'}）", f"承認={a}（期待 {want_a}）")
# 既にある物と同じ作りの新しいエクセルのプログラム＝"派生"（2026-11-09 専務承認・案2）
import tempfile
d = tempfile.mkdtemp()
os.makedirs(os.path.join(d, ".git"))
os.makedirs(os.path.join(d, "tools"))
open(os.path.join(d, "tools", "check_deck.py"), "w").close()
open(os.path.join(d, "old_check.py"), "w").close()
NEW = os.path.join(d, "new_check.py").replace("\\", "/")
derive_cases = [
    ("元の資料：既にあるプログラム", "# 元の資料：old_check.py\nimport openpyxl\nOUT='a.xlsx'\n", "派生"),
    ("元の資料：無いプログラム", "# 元の資料：none_check.py\nimport openpyxl\nOUT='a.xlsx'\n", ""),
    ("元の資料の印なし", "import openpyxl\nOUT='a.xlsx'\n", ""),
]
for name, src, want in derive_cases:
    hit = G.target("Write", {"file_path": NEW, "content": src}, d)
    got = hit[3] if hit else None
    ok = got == want
    bad += not ok
    print(("合格" if ok else "不合格"), name, f"扱い={got or '新規'}（期待 {want or '新規'}）")
print("全部合格" if not bad else f"不合格 {bad}件")
sys.exit(1 if bad else 0)
