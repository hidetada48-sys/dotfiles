# 測らなくてよい返答の試験（7場面）：html-gate.py に作り物の会話の記録を渡し、記録するか（block）しないか（skip）を見る
import json, os, subprocess, sys, tempfile

GATE = os.path.expanduser("~/dotfiles/claude/scripts/html-gate.py")
tmp = tempfile.mkdtemp()


def run(entries, answer):
    """会話の記録（ユーザー発話の並び）と返答から、見張りの判定を返す"""
    path = os.path.join(tmp, "t.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for kind, text, meta in entries:
            e = {"type": kind, "message": {"content": text}}
            if meta:
                e["isMeta"] = True
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
        f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": answer}]}}, ensure_ascii=False) + "\n")
    d = {"transcript_path": path, "session_id": "test"}
    r = subprocess.run([sys.executable, GATE], input=json.dumps(d, ensure_ascii=False).encode("utf-8"), capture_output=True)
    return r.stdout.decode("utf-8").split("\t")[0]


long300 = "コミットとプッシュ、記憶の保存まで済みました。" * 15          # 300字を超える
ok = "直しました。試験は全部合格しています。"                          # 150字以内・伺いなし
s151 = "あ" * 151
ask = "直してよいか、ご承認をお願いします。"

cases = [
    ("1 保存3点ボタンの返答", [("user", "今日の作業をコミット・プッシュ・記憶まで保存して。", False)], long300[:200] + "\n" + "未保存0件です。" * 5, "skip"),
    ("2 朝の取り込みの報告", [("user", "おはよう", False)], "最新の取り込み：dotfiles 変更なし／mino-sakura-hq 更新2件を取り込み\n" + "本日の定例業務は、要対応2件です。" * 8, "skip"),
    ("3 保存の差し戻し後の報告", [("user", "目次", False), ("user", "Stop hook feedback: [bash ~/.claude/scripts/memory-gate.sh]: [保存3点セット] ③記憶が未実施です。", False)], "記憶に保存しました。" * 20, "skip"),
    ("4 種類Aで300字超", [("user", "今日の作業をコミット・プッシュ・記憶まで保存して。", False)], long300, "skip"),
    ("5 種類Bの短い返答", [("user", "どうなった", False)], ok, "skip"),
    ("6 151字の返答", [("user", "どうなった", False)], s151, "block"),
    ("7 150字以内でも伺いで終わる", [("user", "どうなった", False)], ask, "block"),
    ("8 スキル本文の後でも保存の依頼を見分ける", [("user", "今日の作業をコミット・プッシュ・記憶まで保存して。", False), ("user", "Base directory for this skill: x", True)], "あ" * 200, "skip"),
]
bad = 0
for name, ent, ans, want in cases:
    got = run(ent, ans)
    mark = "合格" if got == want else "不合格"
    bad += got != want
    print(f"{mark} {name}：判定={got}（期待={want}）")
print("不合格", bad, "件")
