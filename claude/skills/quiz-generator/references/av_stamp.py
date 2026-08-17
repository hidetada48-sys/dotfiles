#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# answer-validator の「合格スタンプ」発行スクリプト（2026-08-13 新設・恒久ゲート）。
#
# なぜ要るか：
#   answer-validator（答えの中身の2A/2B/2C検証）は Claude のスキルで、コードから起動できない＝
#   「必ず通す」を文章ルールにしていたら Claude が飛ばした（2026-08-13 専務叱責）。
#   そこで「配信の1点（publish_to_drive.sh）」で機械強制する。
#   このスクリプトは、検証したHTMLの中身(sha256)に紐づく合格スタンプ `<html>.av.json` を書く。
#   publish_to_drive.sh は、いま配信するHTMLの sha256 と スタンプの sha256 が一致しなければ配信を拒否する。
#   ＝検証後にHTMLを1文字でも直すとスタンプは無効化され、再検証を強制される（古い検証の使い回しを封じる）。
#
# 使い方（answer-validator の 2A/2B/2C を全問✓にした最後に、Claude が必ず実行する）:
#   python3 av_stamp.py <html> [log.json] [--problems N]
#
# 動作：
#   1. 機械ゲートを再実行（check_leak／log.jsonがあれば check_pitfalls）。落ちたらスタンプを書かない。
#   2. HTML の sha256 を計算し、pass スタンプ `<html>.av.json` を書き出す。
# ※このスクリプトは「機械で判定できる部分」を再確認して指紋を刻むもの。
#   答えの中身（地理・歴史等の正しさ）の担保は 2A/2B/2C（Claudeの検証）が本体で、
#   スタンプはそれを"最終HTMLに対して確かに実施した"ことを sha256 で縛る役割。
import sys, os, json, hashlib, subprocess, datetime

def main():
    # 子プロセスの出力をそのまま転記するので、標準出力も UTF-8 にしておく（2026-08-17）。
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
    args = [a for a in sys.argv[1:]]
    if not args:
        print("使い方: av_stamp.py <html> [log.json] [--problems N]"); return 2
    html = args[0]
    log = ""
    problems = None
    i = 1
    while i < len(args):
        if args[i] == "--problems" and i + 1 < len(args):
            problems = args[i + 1]; i += 2; continue
        if not log and args[i].endswith(".json"):
            log = args[i]
        i += 1
    if not os.path.isfile(html):
        print(f"[NG] HTMLが無い: {html}"); return 2

    ref = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable

    # 子プロセスの出力は必ず UTF-8 で読む（2026-08-17）。
    # text=True だけだと Windows では locale(cp932) で復号され、日本語の出力で
    # UnicodeDecodeError が起きて stdout が取れなくなる（判定は returncode なので
    # 通ってしまうが、失敗時に理由が読めない）。
    RUNOPT = dict(capture_output=True, text=True, encoding="utf-8", errors="replace")

    def _out(r):
        return ((r.stdout or "") + (r.stderr or ""))[-600:]

    # 1) 機械ゲート再実行（落ちたらスタンプを書かない）
    r = subprocess.run([py, f"{ref}/check_leak.py", html], **RUNOPT)
    if r.returncode != 0:
        print("[NG] check_leak が非ゼロ＝答え漏れ。スタンプを発行しない。")
        print(_out(r)); return 1
    if log:
        r2 = subprocess.run([py, f"{ref}/check_pitfalls.py", html, log], **RUNOPT)
        if r2.returncode != 0:
            print("[NG] check_pitfalls が非ゼロ＝つまずき未反映。スタンプを発行しない。")
            print(_out(r2)); return 1

    sha = hashlib.sha256(open(html, "rb").read()).hexdigest()

    # 1.5) 検証レシート（av_report.py の成果物）を要求する（2026-08-17 新設ゲート）。
    #   answer-validator の 2A/2B/完全性 を機械で残した証拠物。無い／sha不一致／
    #   全問未列挙／all_pass でない ときはスタンプを発行しない。
    #   ＝「検証した」と言うだけで証拠を残さず配信、を物理的に封じる。
    receipt_path = html + ".avcheck.json"
    if not os.path.isfile(receipt_path):
        print("[NG] 検証レシートが無い: " + os.path.basename(receipt_path))
        print("     先に `av_report.py <html> <log.json> --rederived <rederived.json>` を通すこと。")
        print("     （answer-validator の 2A/2B/完全性の証拠物。これ無しではスタンプを発行しない）")
        return 1
    try:
        rc = json.load(open(receipt_path, encoding="utf-8"))
    except Exception as e:
        print(f"[NG] 検証レシートが読めない: {e}"); return 1
    if rc.get("html_sha256") != sha:
        print("[NG] 検証レシートの sha256 が現HTMLと不一致＝検証後にHTMLを直したか、別ファイルのレシート。")
        print(f"     レシート={str(rc.get('html_sha256'))[:16]}… / 現HTML={sha[:16]}…  av_report をやり直すこと。")
        return 1
    if not rc.get("all_pass"):
        print("[NG] 検証レシートが all_pass でない（2A/2B/完全性に✗）。修正→av_report 再実行まで発行しない。")
        return 1
    if log:
        try:
            n_log = len(json.load(open(log, encoding="utf-8")).get("questions", []))
            if rc.get("count_log") != n_log:
                print(f"[NG] レシートの出題数({rc.get('count_log')}) と log({n_log}) が不一致。av_report をやり直すこと。")
                return 1
        except Exception:
            pass
    print(f"[OK] 検証レシート照合：all_pass・sha一致（出題{rc.get('count_log')}問）")

    # 2) sha256 を刻んでスタンプ発行
    stamp = {
        "validator": "answer-validator",
        "status": "pass",
        "sha256": sha,
        "html": os.path.basename(html),
        "log": os.path.basename(log) if log else None,
        "problems": int(problems) if (problems and problems.isdigit()) else None,
        "stamped_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    out = html + ".av.json"
    open(out, "w", encoding="utf-8").write(json.dumps(stamp, ensure_ascii=False, indent=2))
    print(f"[OK] answer-validator 合格スタンプを発行: {os.path.basename(out)}")
    print(f"      sha256={sha[:16]}…  以後HTMLを編集するとこのスタンプは無効化され、配信が拒否される。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
