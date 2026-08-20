#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# answer-validator の「検証レシート」発行スクリプト（2026-08-17 新設・恒久ゲート）。
#
# なぜ要るか（2026-08-17 の失敗）：
#   answer-validator（2A/2B/2C）は Claude のスキルで、コードから起動できない。
#   Claude が「検証した」とだけ言って av_stamp を押し、検証の証拠物を一切残さずに
#   配信できてしまった（＝スキルを実際には起動していなかった）。
#   av_stamp は check_leak／check_pitfalls しか見ておらず、「答えの検証をやったか」を要求しない。
#   そこで、答え検証の“機械で判定できる部分”を必ず成果物（レシート）として残させ、
#   av_stamp がそのレシートの実在・sha一致・全問列挙・all_pass を要求する。
#   ＝レシート無しではスタンプできない＝配信まで到達できない。
#
# 使い方（answer-validator の締めに、Claude が必ず実行する）:
#   python3 av_report.py <html> <log.json> --rederived <rederived.json>
#
#   rederived.json ＝ Claude が巻末①を伏せて独立に導いた解答（2A）と 2C 判定を、
#   全 mondai_id ぶん列挙したもの：
#     { "大問1-【1】": {"a": "蘇我氏", "twoC": "ok"},  ... 全問 ... }
#     ・a    … 独立解答（短答型は巻末①と機械突合。記述・図表型は照合不可＝記録のみ「要目視」）
#     ・twoC … 知識検証の判定。★非・計算問題は必須（2026-08-20）＝空だと all_pass にならない。
#              "ok"（web裏取り済）/ "na"（固有名詞・年号なし）/ "要確認"（曖昧・専務目視）/ 任意の注記。
#              ＝2C（固有名詞・年号の裏取り）を飛ばすとレシートが通らず、スタンプ＝配信に到達できない。
#
# 動作：
#   1. 巻末①(.ansrow)・巻末②(.expttl) を HTML から抽出。
#   2. 2B  = 巻末① と 巻末② を正規化して全問一致か（決定論・偽装不可）。
#   3. 完全性 = 巻末①の id 集合 == log の mondai_id 集合／rederived が全 id を覆うか。
#   4. 2A(短答) = rederived.a と 巻末① を正規化して突合（記述・図表型は "要目視" として除外）。
#   5. all_pass ＝ 2B全一致 かつ 完全性OK かつ 2A(短答)全一致。
#   6. <html>.avcheck.json にレシートを書き、all_pass でなければ非ゼロ終了。
import sys, os, re, json, html as _html, hashlib, datetime

# 巻末②が記述で長文のとき、巻末①（短い正答）がその冒頭に含まれるかも見るための型判定。
REVIEW_TYPES = ("記述", "図表", "読み取り", "読取")


def norm(s):
    s = _html.unescape(s or "")
    for ch in " \t　\n\r":
        s = s.replace(ch, "")
    return s.strip()


def is_review(fmt):
    return any(k in (fmt or "") for k in REVIEW_TYPES)


def extract(htmltext):
    ans1, ans2 = {}, {}
    for m in re.finditer(r'<p class="ansrow"><b>(.*?)：</b>\s*(.*?)</p>', htmltext, re.S):
        ans1[_html.unescape(m.group(1)).strip()] = _html.unescape(m.group(2)).strip()
    for m in re.finditer(r'<p class="expttl">(.*?)　答え：(.*?)</p>', htmltext, re.S):
        ans2[_html.unescape(m.group(1)).strip()] = _html.unescape(m.group(2)).strip()
    return ans1, ans2


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
    args = sys.argv[1:]
    if len(args) < 2:
        print("使い方: av_report.py <html> <log.json> --rederived <rederived.json>")
        return 2
    html = args[0]
    log = ""
    rede = ""
    i = 1
    while i < len(args):
        if args[i] == "--rederived" and i + 1 < len(args):
            rede = args[i + 1]; i += 2; continue
        if not log and args[i].endswith(".json"):
            log = args[i]
        i += 1
    for p, name in ((html, "HTML"), (log, "log.json"), (rede, "rederived.json")):
        if not p or not os.path.isfile(p):
            print(f"[NG] {name} が無い: {p}")
            return 2

    htmltext = open(html, encoding="utf-8").read()
    # sha256 は「生バイト」で取る（2026-08-18 修正）。テキスト読みだと Windows で
    # CRLF→LF に変換され、生バイトで見る av_stamp / publish_to_drive と食い違い、
    # 直後にスタンプが必ず拒否される（実際に発生）。配信側の見方に合わせる。
    sha = hashlib.sha256(open(html, "rb").read()).hexdigest()

    # 再発防止（2026-08-18）：answer-validator スキルのステップ0で発行される開始トークンを要求する。
    # ＝スキルを起動せず av_report を直叩きすると、トークンが無く受理しない
    #   （av_begin.py は answer-validator SKILL.md ステップ0 でのみ実行するよう規定）。
    begin = html + ".avbegin.json"
    if not os.path.isfile(begin):
        print("[NG] 開始トークン(.avbegin.json)が無い＝answer-validator スキルのステップ0を"
              "通っていない。av_report を直叩きせず、answer-validator スキルを起動すること。")
        return 2
    try:
        bt = json.load(open(begin, encoding="utf-8"))
    except Exception:
        print("[NG] 開始トークンが壊れている。answer-validator スキルを起動し直すこと。")
        return 2
    if bt.get("html_sha256") != sha:
        print("[NG] 開始トークンの sha が現HTMLと不一致＝トークン発行後にHTMLが変わった/別物。"
              "answer-validator スキルのステップ0(av_begin.py)からやり直すこと。")
        return 2
    try:
        _age = (datetime.datetime.now()
                - datetime.datetime.fromisoformat(bt.get("started_at", ""))).total_seconds()
        if _age > 24 * 3600:
            print("[NG] 開始トークンが古い（24時間超）。answer-validator スキルを起動し直すこと。")
            return 2
    except Exception:
        pass

    ans1, ans2 = extract(htmltext)
    logd = json.load(open(log, encoding="utf-8"))
    qs = logd.get("questions", [])
    fmt_of = {q.get("mondai_id"): q.get("format", "") for q in qs}
    log_ids = [q.get("mondai_id") for q in qs]
    rd = json.load(open(rede, encoding="utf-8"))

    # 完全性
    set_log = set(log_ids)
    set_a1 = set(ans1.keys())
    set_rd = set(rd.keys())
    miss_in_ans1 = sorted(set_log - set_a1)   # 巻末①に無い（＝出題に対し解答一覧が欠落）
    miss_in_rd = sorted(set_log - set_rd)     # rederived に無い（＝2Aを飛ばした問）
    extra_rd = sorted(set_rd - set_log)       # log に無い id を書いた
    completeness_ok = not (miss_in_ans1 or miss_in_rd or extra_rd)

    problems = []
    twoB_all = True
    twoA_all = True
    for qid in log_ids:
        a1 = ans1.get(qid, "")
        a2 = ans2.get(qid, "")
        # 2B: 巻末①と巻末②
        twoB = "✓" if norm(a1) == norm(a2) else "✗"
        if twoB == "✗":
            twoB_all = False
        # 2A: rederived と巻末①（短答型のみ機械突合）
        r = rd.get(qid, {})
        my = r.get("a", "")
        fmt = fmt_of.get(qid, "")
        if is_review(fmt):
            twoA = "要目視(記述)"
        else:
            twoA = "✓" if norm(my) == norm(a1) else "✗"
            if twoA == "✗":
                twoA_all = False
        problems.append(dict(id=qid, format=fmt, ans_listed=a1, ans_exp=a2,
                             twoB=twoB, rederived=my, twoA=twoA, twoC=r.get("twoC", "")))

    # 2C 知識検証の証跡を必須化（2026-08-20 新設・恒久ゲート）。
    #   なぜ要るか（2026-08-20 の失敗）：av_begin/av_report/av_stamp のスクリプトだけ通せば、
    #   2C（固有名詞・年号・数値の web 裏取り）を1件もやらずに合格スタンプが出て配信できた。
    #   ＝レシートは 2A(機械照合)/2B/完全性 しか見ておらず「事実を確かめたか」を要求していなかった。
    #   対策：固有名詞・年号を含みうる「非・計算問題」は rederived に twoC を必ず持たせる。
    #   twoC は "ok"（裏取り済）/"na"（固有名詞・年号なし）/"要確認"（曖昧・専務目視）/任意の注記。
    #   空・未記入なら all_pass にしない＝2C を飛ばすとスタンプが出ず配信に到達できない。
    #   純粋な計算問題（format に「計算」）は固有名詞が無いため 2C 不要（除外）。
    twoC_missing = []
    twoC_review = []
    for qid in log_ids:
        fmt = fmt_of.get(qid, "")
        if "計算" in fmt:
            continue
        v = str(rd.get(qid, {}).get("twoC", "")).strip()
        if not v:
            twoC_missing.append(qid)
        elif v in ("要確認", "要目視", "?"):
            twoC_review.append(qid)
    twoC_ok = not twoC_missing

    all_pass = bool(twoB_all and twoA_all and completeness_ok and twoC_ok)
    receipt = dict(
        validator="av_report",
        html=os.path.basename(html),
        html_sha256=sha,
        log=os.path.basename(log),
        count_log=len(log_ids),
        count_ans_listed=len(ans1),
        twoB_all_pass=twoB_all,
        twoA_short_all_pass=twoA_all,
        completeness_ok=completeness_ok,
        twoC_all_present=twoC_ok,
        twoC_missing=twoC_missing,
        twoC_review=twoC_review,
        all_pass=all_pass,
        problems=problems,
        generated_at=datetime.datetime.now().isoformat(timespec="seconds"),
    )
    out = html + ".avcheck.json"
    open(out, "w", encoding="utf-8").write(json.dumps(receipt, ensure_ascii=False, indent=2))

    print(f"検証レシート: {os.path.basename(out)}  （sha256={sha[:16]}…）")
    print(f"  出題 {len(log_ids)}問 / 巻末① {len(ans1)}件 / rederived {len(rd)}件")
    print(f"  2B(①=②) : {'全一致' if twoB_all else '✗あり'}")
    print(f"  2A(短答) : {'全一致' if twoA_all else '✗あり'}（記述・図表は要目視で除外）")
    print(f"  完全性   : {'OK' if completeness_ok else 'NG'}")
    print(f"  2C(裏取り): {'全問記入' if twoC_ok else 'NG（未記入あり）'}"
          f"{'／要確認 ' + str(len(twoC_review)) + '問' if twoC_review else ''}")
    if twoC_missing:
        print(f"    ✗ twoC 未記入（2Cを飛ばしている）: {twoC_missing[:20]}")
        print("      → 各問の固有名詞・年号を web で裏取りし、rederived に "
              '"twoC":"ok"（または固有名詞なしは "na"）を入れて再実行すること。')
    if miss_in_ans1:
        print(f"    ✗ 巻末①に無い出題: {miss_in_ans1}")
    if miss_in_rd:
        print(f"    ✗ 2A(rederived)を書いていない出題: {miss_in_rd}")
    if extra_rd:
        print(f"    ✗ log に無い id を rederived に記載: {extra_rd}")
    bad = [p["id"] for p in problems if p["twoB"] == "✗" or p["twoA"] == "✗"]
    if bad:
        print(f"    ✗ 不一致の問題: {bad}")
    print(f"  → all_pass = {all_pass}")
    if not all_pass:
        print("[NG] 検証レシートが all_pass でない。修正して再実行すること（スタンプは発行できない）。")
        return 1
    print("[OK] 検証レシート発行。次に av_stamp.py で合格スタンプを発行できる。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
