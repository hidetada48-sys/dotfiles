# 控え帳2の直し（2026-10-22）の試験：
#  ①短い返答（種類B）に専務に通じない言葉の一覧が掛かり、当たれば記録されるか（html-gate.py）
#  ②点検のAIが動かないとき、次の指示で届く記録に1件だけ書かれるか（precheck-answer.py）
# 記録は一時フォルダに書かせ（HTML_GATE_STATE_DIR）、本物の記録には触れない
import json, os, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "html-gate.py")
PRECHECK = os.path.join(HERE, "precheck-answer.py")
tmp = tempfile.mkdtemp()
state = os.path.join(tmp, "state")
env = dict(os.environ, HTML_GATE_STATE_DIR=state, PYTHONIOENCODING="utf-8")
pending = os.path.join(state, "html-gate_pending.log")


def read_pending():
    return open(pending, encoding="utf-8").read() if os.path.exists(pending) else ""


def gate(answer, prompt="確認して"):
    """作り物の会話の記録（専務の発言1つと返答1つ）を見張りに渡し、判定の行を返す"""
    path = os.path.join(tmp, "t.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "user", "message": {"content": prompt}}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": answer}]}}, ensure_ascii=False) + "\n")
    d = {"transcript_path": path, "session_id": "test"}
    r = subprocess.run([sys.executable, GATE], input=json.dumps(d, ensure_ascii=False).encode("utf-8"),
                       capture_output=True, env=env)
    return r.stdout.decode("utf-8").strip()


results = []


def check(name, ok):
    results.append(ok)
    print(("合格" if ok else "不合格") + "：" + name)


# ① 短い返答
if os.path.exists(pending):
    os.remove(pending)
v = gate("定期で作る物は、検証なしで開けます。")
check("短い返答の「定期で作る」を記録する", v.split("\t")[:2] == ["skip", "J"] and "定期で作る" in read_pending())
os.remove(pending)
v = gate("足元の見本を見ているだけです。")
check("短い返答の「足元」を記録する", "足元" in read_pending())
os.remove(pending)
v = gate("直しました。試験は全部合格しています。")
check("一覧の言葉が無い短い返答は記録しない", v.split("\t")[0] == "skip" and read_pending() == "")
v = gate("定期で作る＝定例業務で作るエクセルは、検証なしで開けます。")
check("「＝」の言い換えがある行は記録しない", read_pending() == "")
v = gate("部品で作る物を直してよろしいですか？")
check("伺いで終わる返答（種類Bでない）には、この記録を書かない", read_pending() == "")
v = gate("定期で作る物も含め、保存しました。", prompt="今日の作業をコミット・プッシュ・記憶まで保存して。")
check("保存3点の報告（種類A）には、この記録を書かない", read_pending() == "")

# ② 点検のAIが動かないとき（claude の無い PATH で precheck を動かす）
draft = os.path.join(tmp, "draft.md")
with open(draft, "w", encoding="utf-8") as f:
    f.write("<!-- 中身\nお尋ね：試験\n根拠：試験用\n-->\n試験の返答です。" + str(time.time()) + "\n")
env2 = dict(env, PATH=os.path.dirname(sys.executable))
for _ in range(2):   # 2回測っても記録は1件だけ
    subprocess.run([sys.executable, PRECHECK, draft], capture_output=True, env=env2)
n = read_pending().count("点検のAIが動かなかった")
check("点検のAIが動かないとき記録する（2回測っても1件）", n == 1)

print(f"{sum(results)}/{len(results)} 件合格")
sys.exit(0 if all(results) else 1)
