# 会話の流れでの承認の試験（2026-10-29）：approval-gate.py に作り物の会話の記録を渡し、通す（0）か止める（2）かを見る
import json, os, subprocess, sys, tempfile

GATE = os.path.expanduser("~/dotfiles/claude/hooks/approval-gate.py")
tmp = tempfile.mkdtemp()
EDIT = {"tool_name": "Edit", "tool_input": {"file_path": "C:/Users/miryo/mino-sakura-hq/apps/nippo/store.py"}}
# 控え帳の書き換え（2026-11-03 専務承認：控え帳の削除をはっきり指示されたら伺わずに通す）
HIKAE = {"tool_name": "Bash", "tool_input": {"command": "sed -i '/x/d' ~/dotfiles/claude/hikaecho/hikaecho.jsonl"}}


def run(prev, reply, edit=None):
    """私の直前の発言（prev）と専務のお返事（reply）から、関門の判定（0＝通す・2＝止める）を返す"""
    path = os.path.join(tmp, "t.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "user", "message": {"content": "日報アプリについて"}}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": prev}]}}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"type": "user", "message": {"content": reply}}, ensure_ascii=False) + "\n")
        # お返事のあとの、ツールを呼ぶだけの私の発言とツールの結果（実際の記録と同じ並び）
        f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read"}]}}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}, ensure_ascii=False) + "\n")
    d = dict(edit or EDIT, transcript_path=path, cwd="C:/Users/miryo")
    env = dict(os.environ, HOME=tmp, USERPROFILE=tmp)                      # 試験の判定を本物の記録に残さない
    r = subprocess.run([sys.executable, GATE], input=json.dumps(d, ensure_ascii=False).encode("utf-8"), capture_output=True, env=env)
    return r.returncode


ask = "この直し方で日報アプリを作り直してよろしいですか？"
report = "裏19の行は8行で、決まりの5行を超えたままです。"
diag_ask = "この作りで照合表のエクセルを作ってよろしいですか。クオリティ診断は①体裁だけ／②体裁と中身／診断なし のどれにしますか？"

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
    # クオリティ診断へのお答え（2026-11-09 専務承認・控え帳 11/9 13:41 案2）＝作る伺いへの承認
    ("診断の伺いに 診断なし", diag_ask, "診断なし", 0),
    ("診断の伺いに 体裁だけ", diag_ask, "体裁だけ", 0),
    ("診断の伺いに ②", diag_ask, "②", 0),
    ("診断の伺いに 診断不要", diag_ask, "診断不要", 0),
    ("診断の伺いに 診断なしはだめだ", diag_ask, "いや待て　診断なしはだめだ", 2),
    ("診断の伺いに 問い返し", diag_ask, "体裁だけってなに？", 2),
    ("診断の無い伺いに ①", ask, "①", 2),
    ("伺いの無い所の 診断なし", report, "診断なし", 2),
]
bad = 0
# 控え帳の削除のご指示（伺いの無い所でも、控え帳と削除・消す が同じご発言にあれば通す）
hikae_cases = [
    ("11/3 控え帳 1件目は削除", report, "控え帳　１件目は削除　２件目だけ対処してくれ", 0),
    ("控え帳の2件目を消して", report, "控え帳の2件目を消して", 0),
    ("控え帳 消さない", report, "控え帳は消さないで残せ", 2),
    ("控え帳 削除の言葉なし", report, "控え帳を直してくれ", 2),
    ("控え帳の話でない削除", report, "1件目は削除", 2),
]
# 噛み砕きの合図（2026-11-07 専務承認）：/噛み砕き のあとは資料を作るプログラム（各参謀の scripts）だけ通す
SCRIPT = {"tool_name": "Edit", "tool_input": {"file_path": "/home/x/mino-sakura-hq/production/scripts/shoshi_monthly_yomikata.py"}}
KAMI = "<command-message>噛み砕き</command-message>\n<command-name>/噛み砕き</command-name>\n<command-args>本体22ページの赤</command-args>"
KAMI_EN = "<command-message>噛み砕き</command-message>\n<command-name>/kamikudaki</command-name>\n<command-args></command-args>"
signal_cases = [
    ("/噛み砕き のあとの参謀の scripts", report, KAMI, SCRIPT, 0),
    ("/kamikudaki のあとの参謀の scripts", report, KAMI_EN, SCRIPT, 0),
    ("/噛み砕き のあとでも仕組みのファイルは止める", report, KAMI, EDIT, 2),
    ("合図なしの参謀の scripts", report, "日報の資料を直してくれ", SCRIPT, 2),
    ("ほかのスラッシュの合図", report, "<command-name>/effort</command-name>", SCRIPT, 2),
]
for name, prev, reply, edit, want in signal_cases:
    got = run(prev, reply, edit)
    ok = got == want
    bad += not ok
    print(("合格" if ok else "不合格"), name, "→", {0: "通す", 2: "止める"}.get(got, got))
cases_n = len(signal_cases)
for name, prev, reply, want in hikae_cases:
    got = run(prev, reply, HIKAE)
    ok = got == want
    bad += not ok
    print(("合格" if ok else "不合格"), name, "→", {0: "通す", 2: "止める"}.get(got, got))
for name, prev, reply, want in cases:
    got = run(prev, reply)
    ok = got == want
    bad += not ok
    print(("合格" if ok else "不合格"), name, "→", {0: "通す", 2: "止める"}.get(got, got))
print(f"{len(cases) + len(hikae_cases) + cases_n - bad}/{len(cases) + len(hikae_cases) + cases_n} 合格")
sys.exit(1 if bad else 0)
