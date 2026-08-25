"""統合設計シート＝模試の承認ターンを1枚に集約する（2026-08-21 新設）。

背景＝承認ターンが ①コア項目 ②構成・配点 ③難易度割合 の3つに分かれ、専務が
内容・配点・難易度を同時に見られず、曖昧承認や③を見てからの内容手戻りが起きていた。
そこで①②③を1枚のHTMLに統合し、集計（配点・難易度構成比と応用基準の可否・規模の
下限照合・由来内訳）を機械が自動計算・自動判定して同時に見せ、1回で承認する。

入力＝設計データJSON（承認用の一次ソース。承認後そのまま出題履歴JSONの骨格に流用できる）:
{
  "subject": "理科", "unit": "...", "level": "応用",
  "difficulty_primary": "complexity" | "process",
  "total_points": 100, "time_limit": 50,
  "description_volume": "標準", "mix_type": "ひっかけ特訓",
  "scale_key": "理科",              # 省略時は subject を使う（_scale.json 照合キー）
  "brief_dir": "/abs/path/期末模試_設計ブリーフ",  # 省略時は環境変数 DESIGN_BRIEF のディレクトリ
  "daimon": [
    {"no":1,"title":"密度→物質特定","time":10,
     "q":[{"id":"大問1(1)","brief":"メスシリンダーの読み方","format":"知識",
           "point":3,"load":"recall","complexity":"low",
           "pitfall":"後目盛りをそのまま体積に","source":"④⑤"}, ...]},
    ...
  ]
}

使い方:
    python build_design_sheet.py <設計データJSON> [出力HTML]
    出力を省略すると同じ場所に <名前>_設計シート.html を書く。

集計と判定は check_difficulty.py / check_calibration.py と同じしきい値を使う
（承認時点で機械ゲートと同じ目で見えるようにする＝後段のゲートで初めて弾かれるのを防ぐ）。
"""
import json
import os
import re
import sys
from collections import Counter
from html import escape

# 応用/標準のしきい値（check_difficulty.py と揃える）
THRESHOLDS = {
    # ★2026-08-23：mid（recall）は応用ではない → 応用は high（construct）主体に締めた。
    "complexity": {  # 主軸=内容の複雑さ
        "応用": lambda c, n: (c["low"] == 0 and c["high"]/n >= 0.60),
        "標準": lambda c, n: (c["low"]/n <= 0.55 and c["high"] >= 1),
        "keys": ["low", "mid", "high"],
        "label": "内容の複雑さ",
        "rule": {"応用": "low=0 / high≥60%（midは応用でない）", "標準": "low≤55% / high≥1問"},
    },
    "process": {  # 主軸=思考の種類
        # ★第8次（2026-08-25）＝recall=0 は撤回。応用の主判定は「再認をほぼ置かない」へ移した
        #   （下の recognition 集計で別途判定する。ここは construct 下限だけを見る）。
        "応用": lambda c, n: (c["construct"]/n >= 0.40),
        "標準": lambda c, n: (c["recall"]/n <= 0.55 and c["construct"] >= 1),
        "keys": ["recall", "select", "construct"],
        "label": "思考の種類",
        "rule": {"応用": "construct≥40%（＋再認≤15%は別枠で判定）", "標準": "recall≤55% / construct≥1問"},
    },
}


def load_scale(brief_dir, key):
    """_scale.json から教科の小問数下限を引く（無ければ None）。"""
    if not brief_dir:
        return None
    p = os.path.join(brief_dir, "_scale.json")
    if not os.path.isfile(p):
        return None
    try:
        return json.load(open(p, encoding="utf-8")).get(key)
    except Exception:
        return None


def build(data):
    primary = data.get("difficulty_primary", "process")
    level = data.get("level", "標準")
    T = THRESHOLDS.get(primary, THRESHOLDS["process"])
    dkey = "complexity" if primary == "complexity" else "load"

    # 全小問を平坦化
    allq = []
    for d in data["daimon"]:
        for q in d["q"]:
            allq.append(q)
    n = len(allq)

    # 集計
    pts = sum(q["point"] for q in allq)
    tm = sum(d.get("time", 0) for d in data["daimon"])
    dist = Counter(q.get(dkey, "") for q in allq)
    for k in T["keys"]:
        dist.setdefault(k, 0)
    src = Counter()
    for q in allq:
        for ch in q.get("source", ""):
            if ch in "③④⑤":
                src[ch] += 1

    # 判定
    tp = data.get("total_points", 100)
    tl = data.get("time_limit", 50)
    ok_pts = (pts == tp)
    ok_time = (tm == tl)
    passed = T[level](dist, n) if n and level in T and callable(T.get(level)) else False
    scale_key = data.get("scale_key") or data.get("subject", "")
    brief_dir = data.get("brief_dir") or (os.path.dirname(os.environ.get("DESIGN_BRIEF", "")) or "")
    min_q = load_scale(brief_dir, scale_key)
    ok_scale = (min_q is None) or (n >= int(min_q))

    # ★A（2026-08-24 第5次改修に追随）：応用で禁止するのは「純二択（○×・正誤・2択）」だけ。
    #   選択問題そのもの（誤り選び・並べ替え・3択以上）はヒントが無ければ可＝ここでも
    #   check_difficulty.py の同一関数 is_binary_format で判定する（シート緑＝配信緑・ドリフト防止）。
    #   ヒントの有無は下の「設問文の点検」（check_hint 由来）が別途担保する。
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from check_difficulty import is_binary_format
        choice_qs = ([q.get("id", "?") for q in allq
                      if is_binary_format(q.get("format"))]
                     if level == "応用" else [])
    except Exception:
        choice_qs = []
    ok_choice = (len(choice_qs) == 0)
    # ★第8次（2026-08-25）＝応用(process)の主判定＝「候補を手渡した問い(再認)」の比率。
    #   check_difficulty.py と同じ関数で数える（シート緑＝配信緑）。
    rec_qs, ok_recog, rec_max = [], True, 15
    if primary != "complexity":
        try:
            from check_difficulty import has_choices, RECOGNITION_MAX_PCT
            rec_max = RECOGNITION_MAX_PCT
            rec_qs = [q.get("id", "?") for q in allq if has_choices(q)]
            if level == "応用":
                ok_recog = (n > 0 and len(rec_qs) / n * 100 <= rec_max + 1e-9)
        except Exception:
            pass
    # 参考表示用＝選択形式（純二択以外も含む）の件数。禁止ではなく可視化のみ。
    _SEL = ("選択", "記号", "誤り選び", "並べ替え", "並べかえ", "択一", "組合せ",
            "組み合わせ", "多肢", "choice")
    sel_qs = [q.get("id", "?") for q in allq
              if any(m.lower() in str(q.get("format", "")).lower() for m in _SEL)]

    # ★第4次改修：応用の select/construct が“本物”か（answer_mode/links）を、
    #   check_difficulty.py の同一関数で判定（自前しきい値のドリフトを防ぐ・シート緑＝配信緑）。
    genuine_bad = []
    if level == "応用" and primary != "complexity":
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from check_difficulty import genuine_advanced_violations
            norm = [{"mondai_id": q.get("id", "?"), "load": q.get("load"),
                     "answer_mode": q.get("answer_mode"), "links": q.get("links")} for q in allq]
            genuine_bad = genuine_advanced_violations(norm)
        except Exception as e:
            genuine_bad = [f"    ・検査不能: {e}"]
    ok_genuine = (len(genuine_bad) == 0)

    # ★2026-08-24：設問文そのものを承認ターンで点検する（要約=brief だけを見せていたため、
    #   文言に混入したヒントが承認の場に出ず、専務が解いて初めて見つかる状態だった）。
    #   判定語は check_hint.py から取り込む（配信ゲートと同じ目で見る＝ドリフト防止）。
    no_prompt, hint_hits, declared, core_hits, no_core = [], [], [], [], []
    proc_hits, long_hits, ilens = [], [], []
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from check_hint import (VIEWPOINT_PATTERNS, COUNT_PATTERNS, core_overlap,
                                PROCEDURE_RULES, instruction_len, LEN_NG, COMMA_NG,
                                ATTACH_RULES, LEN_NG_PROCESS, COMMA_NG_PROCESS)
        _hard = str(level) in ("応用", "発展")
        _proc = (primary != "complexity")
        LEN_NG = LEN_NG_PROCESS if (_proc and _hard) else LEN_NG
        COMMA_NG = COMMA_NG_PROCESS if (_proc and _hard) else COMMA_NG
        for q in allq:
            qid = q.get("id", "?")
            text = str(q.get("prompt") or "")
            if not text:
                no_prompt.append(qid)
                continue
            hits = [pt for pt in (VIEWPOINT_PATTERNS + COUNT_PATTERNS) if re.search(pt, text)]
            if hits:
                hint_hits.append(qid)
            if str(q.get("hint_reason") or "").strip():
                declared.append(qid)
            # ★2026-08-25：答えの中核語の重なりを承認の場でも見る。
            #   配信ゲート（check_hint）だけが見ていたため、承認シートは緑のまま出せた＝
            #   英語で「答えの英文を応答文として設問に見せる」型の誤りが、専務の目に頼る状態だった。
            # ★2026-08-25 第7次：手順の誘導と設問文の長さも承認の場で見る。
            #   背景＝設問文は読んでいたが、見ていたのは決まった型だけで、
            #   「〜を求め、〜し、〜を書きなさい」も 72字の長文も素通りしていた。
            ph = [lab for pat, lab in PROCEDURE_RULES if re.search(pat, text)]
            if ph:
                proc_hits.append(f'{qid}（{ph[0]}）')
            # ★第8次：付帯指示句＝答えの目次を渡していないか
            ah = [lab for pat, lab in ATTACH_RULES if re.search(pat, text)]
            if ah:
                proc_hits.append(f'{qid}（{ah[0]}）')
            il = instruction_len(text); ilens.append(il)
            if il > LEN_NG or text.count("、") >= COMMA_NG:
                long_hits.append(f'{qid}（指示{il}字'
                                 + (f'・読点{text.count("、")}個' if text.count("、") >= COMMA_NG else '')
                                 + '）')
            undecl, found = core_overlap(text, q)
            if undecl:
                no_core.append(qid)
            elif found:
                core_hits.append(f'{qid}（{" ".join(found[:4])}）')
    except Exception as e:
        no_prompt = [f"検査不能: {e}"]
    undeclared = [x for x in hint_hits if x not in declared]
    hard = str(level) in ("応用", "発展")
    ok_prompt = (len(no_prompt) == 0 and len(undeclared) == 0 and len(core_hits) == 0
                 and len(proc_hits) == 0 and len(long_hits) == 0
                 and not (hard and no_core))

    return dict(no_prompt=no_prompt, hint_hits=hint_hits, declared=declared,
                core_hits=core_hits, no_core=no_core,
                proc_hits=proc_hits, long_hits=long_hits, ilens=ilens,
                undeclared=undeclared, ok_prompt=ok_prompt,allq=allq, n=n, pts=pts, tm=tm, dist=dist, src=src, primary=primary,
                level=level, T=T, dkey=dkey, ok_pts=ok_pts, ok_time=ok_time,
                passed=passed, min_q=min_q, ok_scale=ok_scale, tp=tp, tl=tl,
                choice_qs=choice_qs, ok_choice=ok_choice, sel_qs=sel_qs,
                rec_qs=rec_qs, ok_recog=ok_recog, rec_max=rec_max,
                genuine_bad=genuine_bad, ok_genuine=ok_genuine)


def mark(ok):
    return ('<span style="color:#127a2e;font-weight:700">✓</span>' if ok
            else '<span style="color:#c0142b;font-weight:700">✗ 要修正</span>')


def render(data, s):
    subject = escape(str(data.get("subject", "")))
    unit = escape(str(data.get("unit", "")))
    head = (f'{subject}　{escape(str(data.get("level","")))}／{s["tp"]}点・{s["tl"]}分／'
            f'主軸＝{s["T"]["label"]}／{escape(str(data.get("mix_type","")))}／記述{escape(str(data.get("description_volume","")))}')

    # 難易度の内訳文字列
    dbits = " ／ ".join(f'{k} {s["dist"][k]}問({s["dist"][k]/s["n"]*100:.0f}%)' for k in s["T"]["keys"])
    rule = s["T"]["rule"].get(s["level"], "")

    css = """
    *{box-sizing:border-box}
    body{margin:0;background:#f2f3f5;color:#1a1a1a;font-family:"Yu Gothic","Hiragino Kaku Gothic ProN",sans-serif}
    .page{max-width:1000px;margin:14px auto;padding:22px 26px;background:#fff;box-shadow:0 2px 14px rgba(0,0,0,.14)}
    h1{font-size:18pt;color:#1f4e79;margin:0 0 2px}
    .sub{color:#666;margin:0 0 16px;font-size:11pt}
    .cards{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:18px}
    .card{flex:1;min-width:210px;border:1px solid #d5dde6;border-radius:8px;padding:10px 14px;background:#fafcff}
    .card h3{margin:0 0 6px;font-size:10.5pt;color:#1f4e79}
    .card .big{font-size:13pt;font-weight:700}
    .card .sm{font-size:10pt;color:#555;line-height:1.6}
    table{border-collapse:collapse;width:100%;margin:6px 0 20px;font-size:10.3pt}
    th,td{border:1px solid #d5dde6;padding:5px 8px;text-align:left;vertical-align:top}
    th{background:#eef3f8;color:#1f4e79}
    td.n{text-align:center;width:30px;color:#1f4e79;font-weight:700}
    td.c{text-align:center;white-space:nowrap}
    .cx-low{color:#127a2e}.cx-mid{color:#b8860b}.cx-high{color:#c0142b;font-weight:700}
    .dsec{font-weight:700;color:#1f4e79;margin:16px 0 4px}
    .note{color:#888;font-size:10pt;margin-top:14px}
    """
    out = ['<!doctype html><html lang="ja"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           f'<title>統合設計シート {subject}</title><style>{css}</style></head><body><div class="page">']
    out.append(f'<h1>統合設計シート（承認用・1回で承認）</h1>')
    out.append(f'<p class="sub">{head}<br>{unit}</p>')

    # サマリーカード
    out.append('<div class="cards">')
    out.append(f'<div class="card"><h3>配点・時間</h3>'
               f'<div class="big">{s["pts"]}点 / {s["tm"]}分</div>'
               f'<div class="sm">配点 {mark(s["ok_pts"])}（宣言{s["tp"]}）　時間 {mark(s["ok_time"])}（宣言{s["tl"]}）</div></div>')
    out.append(f'<div class="card"><h3>難易度（{s["T"]["label"]}）／{s["level"]}判定 {mark(s["passed"])}</h3>'
               f'<div class="sm">{dbits}<br>基準：{escape(rule)}</div></div>')
    if s["level"] == "応用":
        cq = s["choice_qs"]
        nsel = len(s.get("sel_qs", []))
        detail = (f'純二択なし（選択問題 {nsel}問はヒント検査で担保）' if s["ok_choice"]
                  else f'純二択 {len(cq)}問（{escape("、".join(str(x) for x in cq[:10]))}）')
        out.append(f'<div class="card"><h3>応用の形式（純二択のみ禁止）{mark(s["ok_choice"])}</h3>'
                   f'<div class="sm">{detail}<br>選択問題は可・純二択（○×/正誤/2択）だけ不可</div></div>')
        if s.get("primary") != "complexity":
            nrec = len(s.get("rec_qs") or [])
            rp = nrec / s["n"] * 100 if s["n"] else 0
            rdetail = (f'候補を手渡した設問 {nrec}問（{rp:.0f}%）／自由想起 {s["n"] - nrec}問'
                       f'<br>上限{s.get("rec_max", 15)}%＝選択肢は並べ替え等、選択でしか成立しない形だけに'
                       + ('' if s["ok_recog"] else
                          '<br>' + escape("、".join(str(x) for x in (s.get("rec_qs") or [])[:12]))))
            out.append(f'<div class="card"><h3>応用の主判定＝再認の少なさ{mark(s["ok_recog"])}</h3>'
                       f'<div class="sm">{rdetail}</div></div>')
        gdetail = ("本物（想起でなく導出/転移・複数を結合）" if s["ok_genuine"]
                   else f'ニセ応用 {len(s["genuine_bad"])}件（answer_mode/links 不足）')
        out.append(f'<div class="card"><h3>応用の本物さ（mode/links）{mark(s["ok_genuine"])}</h3>'
                   f'<div class="sm">{gdetail}<br>単一事実の想起は応用でない（複数を結ぶ／初見に当てはめる）</div></div>')
    sc = (f'下限{s["min_q"]} ≤ {s["n"]}問' if s["min_q"] is not None else f'{s["n"]}問（下限定義なし）')
    out.append(f'<div class="card"><h3>規模</h3><div class="big">{s["n"]}問</div>'
               f'<div class="sm">{sc}　{mark(s["ok_scale"])}</div></div>')
    srcs = "／".join(f'{k}{s["src"].get(k,0)}件' for k in "③④⑤")
    out.append(f'<div class="card"><h3>由来（③間違い ④落とし穴 ⑤ブリーフ）</h3>'
               f'<div class="sm">{srcs}</div></div>')
    il = s.get("ilens") or [0]
    pm = (f'ヒント語 {len(s["hint_hits"])}件（申告 {len(s["declared"])}件・'
          f'未申告 {len(s["undeclared"])}件）／答えの中核語の重なり {len(s["core_hits"])}件'
          f'／手順の誘導 {len(s["proc_hits"])}件／長すぎる設問文 {len(s["long_hits"])}件'
          f'／指示のことば 平均{sum(il)//len(il)}字・最長{max(il)}字'
          + (f'／answer_core 未宣言 {len(s["no_core"])}件' if s["no_core"] else '')
          if not s["no_prompt"]
          else f'設問文(prompt)未記載 {len(s["no_prompt"])}件')
    for lab, key in (("手順の誘導", "proc_hits"), ("長すぎ", "long_hits")):
        if s.get(key):
            pm += "　＜" + lab + "＞" + "、".join(str(x) for x in s[key][:6])
    out.append(f'<div class="card"><h3>設問文の点検</h3><div class="sm">{escape(pm)}　'
               f'{mark(s["ok_prompt"])}</div>'
               + (f'<div class="sm">重なり: {escape("／".join(s["core_hits"][:6]))}'
                  '<br>＝答えの決め手を設問が渡している（英語なら答えの英文を見せている）</div>'
                  if s["core_hits"] else '')
               + '</div>')
    out.append('</div>')

    # 大問ごとの小問明細（通しNo.）
    no = 0
    for d in data["daimon"]:
        dp = sum(q["point"] for q in d["q"])
        out.append(f'<div class="dsec">大問{d["no"]}　{escape(str(d.get("title","")))}'
                   f'（{dp}点・{d.get("time","?")}分・{len(d["q"])}問）</div>')
        # ★2026-08-25：リード文・共通の式セット（lead/expr）も承認の場に出す。
        #   これが無いと選択肢セットを使う問い（完答・記号選択）を専務が判断できない。
        for key, lb in (("lead", "リード文"), ("expr", "共通の式・資料")):
            v = str(d.get(key) or "").strip()
            if v:
                out.append(f'<div style="margin:2px 0 6px;padding:6px 8px;background:#f6f6f2;'
                           f'border-left:3px solid #bbb;font-size:10pt">〔{lb}〕{escape(v)}</div>')
        out.append('<table><tr><th>No</th><th>内容</th><th>形式</th><th>配点</th>'
                   f'<th>{s["T"]["label"]}</th><th>狙うつまずき</th></tr>')
        for q in d["q"]:
            no += 1
            lab = q.get(s["dkey"], "")
            cls = f'cx-{lab}' if s["primary"] == "complexity" else ''
            # 応用の select/construct は「認知の担保」（mode＋結びつける要素）を明示＝盛りを見えるようにする
            ml = ""
            if s["level"] == "応用" and s["primary"] != "complexity" and q.get("load") in ("select", "construct"):
                lk = q.get("links")
                lkstr = "・".join(str(x) for x in lk) if isinstance(lk, (list, tuple)) else str(lk or "—")
                ml = (f'<br><span style="color:#888;font-size:9pt">〔{escape(str(q.get("answer_mode","?")))}'
                      f'／結合: {escape(lkstr)}〕</span>')
            # ★2026-08-24：要約(brief)ではなく設問文の全文を出す。ヒントは文言に混入するため、
            #   要約を見せている限り承認の場では見つけられない。
            prompt = str(q.get("prompt") or "")
            if prompt:
                body = escape(prompt)
                ch = str(q.get("choices") or "").strip()
                if ch:  # ★2026-08-25：選択肢も承認の場に出す（実物と同じものを見て判断できるように）
                    body += f'<br><span style="color:#333">{escape(ch)}</span>'
                body += (f'<br><span style="color:#888;font-size:9pt">〔要約〕'
                         f'{escape(str(q.get("brief","")))}</span>')
            else:
                body = (f'{escape(str(q.get("brief","")))}'
                        f'<br><span style="color:#c0142b;font-size:9pt">※設問文(prompt)未記載</span>')
            hr = str(q.get("hint_reason") or "").strip()
            if hr:
                body += (f'<br><span style="color:#b06a00;font-size:9pt">〔観点を足した理由〕'
                         f'{escape(hr)}</span>')
            ac = q.get("answer_core")
            if ac:
                acs = "・".join(str(x) for x in ac) if isinstance(ac, (list, tuple)) else str(ac)
                body += (f'<br><span style="color:#888;font-size:9pt">〔採点の合格条件〕'
                         f'{escape(acs)}</span>')
            out.append(f'<tr><td class="n">{no}</td><td>{body}{ml}</td>'
                       f'<td class="c">{escape(str(q.get("format","")))}</td>'
                       f'<td class="c">{q["point"]}</td>'
                       f'<td class="c {cls}">{escape(lab)}</td>'
                       f'<td>{escape(str(q.get("pitfall","")))}</td></tr>')
        out.append('</table>')

    out.append('<p class="note">※ この1枚で内容・配点・難易度・規模・由来を同時に確認できます。'
               '修正は「No.◯を〜」と番号で指示してください（再生成して集計し直します）。'
               '緑✓＝基準を満たす／赤✗＝配信ゲートで止まる（承認前に直す）。</p>')
    out.append('</div></body></html>')
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.stdout.reconfigure(encoding="utf-8")
    src = sys.argv[1]
    data = json.load(open(src, encoding="utf-8"))
    s = build(data)
    html = render(data, s)
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + "_設計シート.html"
    open(out, "w", encoding="utf-8").write(html)
    # コンソールにも要点を出す（承認前に自分で確認する用）
    print(f"設計シート: {out}")
    print(f"  規模 {s['n']}問（下限{s['min_q']}）: {'OK' if s['ok_scale'] else 'NG'}")
    print(f"  配点 {s['pts']}/{s['tp']}: {'OK' if s['ok_pts'] else 'NG'} / 時間 {s['tm']}/{s['tl']}: {'OK' if s['ok_time'] else 'NG'}")
    dbits = " ".join(f"{k}{s['dist'][k]}" for k in s["T"]["keys"])
    print(f"  難易度({s['primary']}/{s['level']}) {dbits}: {'OK' if s['passed'] else 'NG'}")
    if s["no_prompt"]:
        print(f"  設問文の点検: NG（prompt 未記載 {len(s['no_prompt'])}件＝承認に全文を出せない）")
    else:
        il2 = s.get("ilens") or [0]
        print(f"  設問文の点検: ヒント語 {len(s['hint_hits'])}件"
              f"（申告 {len(s['declared'])}件・未申告 {len(s['undeclared'])}件）"
              f"／中核語の重なり {len(s['core_hits'])}件"
              f"／手順の誘導 {len(s['proc_hits'])}件／長すぎる設問文 {len(s['long_hits'])}件"
              f"／指示 平均{sum(il2)//len(il2)}字・最長{max(il2)}字"
              f"／answer_core 未宣言 {len(s['no_core'])}件"
              f": {'OK' if s['ok_prompt'] else 'NG'}")
        for x in s['core_hits'][:6]:
            print(f"    ・重なり {x}")
    if s["level"] == "応用":
        nsel = len(s.get("sel_qs", []))
        if s.get("primary") != "complexity":
            nrec = len(s.get("rec_qs") or [])
            rp = nrec / s["n"] * 100 if s["n"] else 0
            print(f"  応用の主判定＝再認の少なさ: {'OK' if s['ok_recog'] else 'NG'}"
                  f"（候補を手渡した設問 {nrec}問 {rp:.0f}% / 上限{s.get('rec_max',15)}%）")
        print(f"  応用の形式（純二択のみ禁止）: {'OK（選択問題' + str(nsel) + '問・純二択0）' if s['ok_choice'] else 'NG（純二択=' + str(len(s['choice_qs'])) + '問）'}")
        if s["primary"] != "complexity":
            if s["ok_genuine"]:
                print("  応用の本物さ（mode/links）: OK（想起でなく導出/転移・複数を結合）")
            else:
                print(f"  応用の本物さ（mode/links）: NG（ニセ応用 {len(s['genuine_bad'])}件）")
                for line in s["genuine_bad"][:30]:
                    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
