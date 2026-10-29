# 会話の流れでの承認の試験（2026-10-29）：approval-gate.py に作り物の会話の記録を渡し、通す（0）か止める（2）かを見る
import json, os, subprocess, sys, tempfile

GATE = os.path.expanduser("~/dotfiles/claude/hooks/approval-gate.py")
tmp = tempfile.mkdtemp()
EDIT = {"tool_name": "Edit", "tool_input": {"file_path": "C:/Users/miryo/mino-sakura-hq/apps/nippo/store.py"}}


def run(prev, reply):
    """私の直前の発言（prev）と専務のお返事（reply）から、関門の判定（0＝通す・2＝止める）を返す"""
    path = os.path.join(tmp, "t.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "user", "message": {"content": "日報アプリについて"}}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": prev}]}}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"type": "user", "message": {"content": reply}}, ensure_ascii=False) + "\n")
        # お返事のあとの、ツールを呼ぶだけの私の発言とツールの結果（実際の記録と同じ並び）
        f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read"}]}}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}, ensure_ascii=False) + "\n")
    d = dict(EDIT, transcript_path=path, cwd="C:/Users/miryo")
    env = dict(os.environ, HOME=tmp, USERPROFILE=tmp)                      # 試験の判定を本物の記録に残さない
    r = subprocess.run([sys.executable, GATE], input=json.dumps(d, ensure_ascii=False).encode("utf-8"), capture_output=True, env=env)
    return r.returncode


ask = "この直し方で日報アプリを作り直してよろしいですか？"
report = "裏19の行は8行で、決まりの5行を超えたままです。"

cases = [
    # 実際に止まった事例（伺いへのお返事）＝通す
    ("10/14 もどせ", "変更を戻すプログラムも保存します。よろしければ「承認」とお返事ください。", "変更方針　承認を得ずに実施したな　もどせ！！", 0),
    ("10/27 お前が消せ", "「使用中_書き込み.txt」を消していただければ進めます。", "お前が消せ", 0),
    ("10/28 23:16 〜にしろ", "②と①の直しを行ってよろしいですか。",
     "”直し方：確認待ちが2件以上あるときは、自動で切り替えず、最初の画面に留めます。”？\n\n枠の中””読み取り終わりました確認してください”　青ボタンを並べる”9/9””10/29””にしろ", 0),
    ("伺いに はい", ask, "はい", 0),
    ("伺いに いいよ", ask, "いいよ", 0),
    ("伺いに 直して", ask, "直して", 0),
    ("伺いに 並べろ", ask, "確定した順に並べろ", 0),
    ("伺いに 承認（今まで）", ask, "承認", 0),
    ("伺いの後の太字の伺い", "直し方は次のとおりです。\n\n**この直し方で直してよろしいですか？**", "やれ", 0),
    # 止める
    ("10/5 伺いの無い 直してくれ", report, "日報アプリを直してくれ", 2),
    ("10/28 11:47 伺いの無い 並べろ", report, "そうではない　確定した順に並べろ", 2),
    ("伺いに 打ち消し", ask, "いや、待て", 2),
    ("伺いに 違う", ask, "違う　確定した順だ", 2),
    ("伺いに 問い返し", ask, "それで何が変わるの？", 2),
    ("伺いに なぜ", ask, "なんで足すんや", 2),
    ("伺いに 関係ない話", ask, "ところで在庫の数字", 2),
    ("伺いに それ", ask, "なにそれ", 2),
    ("伺いに 直っていない", ask, "直っていない", 2),
]
bad = 0
for name, prev, reply, want in cases:
    got = run(prev, reply)
    ok = got == want
    bad += not ok
    print(("合格" if ok else "不合格"), name, "→", {0: "通す", 2: "止める"}.get(got, got))
print(f"{len(cases) - bad}/{len(cases)} 合格")
sys.exit(1 if bad else 0)
