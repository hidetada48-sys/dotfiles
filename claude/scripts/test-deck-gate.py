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
]
bad = 0
for name, evs, want_d, want_a in cases:
    d = G.diagnosis(evs)[0]
    a = G.agreed_after_plan(evs)
    ok = d == want_d and a == want_a
    bad += not ok
    print(("合格" if ok else "不合格"), name, f"診断={d or 'なし'}（期待 {want_d or 'なし'}）", f"承認={a}（期待 {want_a}）")
print("全部合格" if not bad else f"不合格 {bad}件")
sys.exit(1 if bad else 0)
