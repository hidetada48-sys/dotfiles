"""設問文に「答えの決め手（ヒント）」が埋め込まれていないかを、配信するHTMLそのものから検査する。

**なぜHTMLを読むのか（2026-08-24 新設の理由）**
これまで難易度の関門（check_difficulty.py）は出題履歴JSONしか読まず、**設問文を一度も見て
いなかった**。check_leak.py は設問文を読んでいたが、①「設問文一致は終了コードに含めない」と
無効化されており、②答えの先頭N文字の部分一致方式のため記述式では当たらない（実際、全問記述の
地理ver2に流すと 0件・終了コード0 で素通りした）。
そこで本スクリプトは **生徒が受け取る紙（HTML）そのもの** を読む。JSONは書き手の自己申告で、
HTMLと違う"きれいな文"を書けてしまうため、JSONの prompt とHTMLの本文を**突合**もする。

検査する4つ（level=応用 は違反1件で終了コード1＝配信拒否）:
  〔1〕観点の手渡し … 「〜にふれて」「〜から説明」「〜の読み取りから」など、
       生徒が自分で立てるべき見分ける観点を設問側が渡している表現。
       → `hint_reason` を宣言していれば通す（件数は必ず表示する＝黙って足せなくする）。
  〔2〕答えの中核語の重なり … `answer_core`（採点の合格条件となる語）が設問文に出ている。
       → **宣言があっても NG**（答えそのものを渡しているため）。
  〔3〕個数の先出し … 「温帯は3つの区分に分けられる」のように区分数を教えている。
       → `hint_reason` があれば通す。
  〔4〕宣言なきヒント … 〔1〕〔3〕に当たるのに `hint_reason` が無い。

使い方:
    python check_hint.py <問題集HTML> <出題履歴JSON>

終了コード: level=応用 で違反があれば 1、それ以外は 0（標準・基本は件数を表示するだけ）。
"""
import html as _html
import json
import re
import sys

# 〔1〕観点の手渡し表現。設問側が「どこを見て答えるか」を指定してしまうもの。
VIEWPOINT_RULES = [
    (r"にふれて|に触れて|にもふれて", "〜にふれて"),
    (r"から説明|から答え|から述べ", "〜から説明/答え"),
    (r"読み取りから|読みとりから", "〜の読み取りから"),
    (r"に着目|に注目", "〜に着目"),
    (r"を手がかり|をヒントに", "〜を手がかりに"),
    (r"の(?:ちがい|違い)がはっきりわかるように", "違いがわかるように"),
    (r"両方に", "両方にふれて"),
    (r"それぞれ1つずつあげ", "それぞれ1つずつ"),
    (r"と結びつけて", "〜と結びつけて"),
    (r"[『「][^』」]{2,20}[』」]\s*[『「][^』」]{2,20}[』」]", "観点を鍵かっこで列挙"),
]
VIEWPOINT_PATTERNS = [r for r, _ in VIEWPOINT_RULES]

# 〔3〕個数の先出し。
COUNT_PATTERNS = [
    r"[0-9０-９一二三四五六七八九十]\s*つの(?:区分|種類|グループ|型)に(?:分け|分類)",
    r"[0-9０-９一二三四五六七八九十]\s*つに(?:分け|分類)される",
]

# 〔2〕で無視する汎用語（answer_core に混ざっても重なり判定に使わない）。
GENERIC = {"気候", "説明", "理由", "特徴", "地域", "人々", "生活", "japan", "日本",
           "違い", "ちがい", "関係", "変化", "影響", "工夫", "問題"}

# 英語の機能語。answer_core が英文になる英語では、これらが設問文に出ても「答えを渡した」ことに
# ならない（例：設問文の「be動詞を使って」と answer_core の be が当たる＝誤検知）。
# 内容語（動詞・名詞・数詞）だけで判定させるために除外する（2026-08-25）。
STOP_EN = {"is", "am", "are", "was", "were", "be", "do", "does", "did", "not", "no", "yes",
           "the", "a", "an", "this", "that", "these", "those", "to", "of", "in", "on", "at",
           "for", "with", "and", "or", "but", "it", "he", "she", "they", "we", "you", "i",
           "his", "her", "their", "our", "your", "my", "me", "him", "them", "us",
           "what", "when", "where", "who", "whose", "which", "how", "why", "can", "will"}

MIN_TERM = 2  # 重なり判定に使う語の最短文字数


def strip_tags(x):
    return re.sub(r"<[^>]+>", "", x)


def norm(s):
    """比較用の正規化（実体参照を戻し、空白・全角空白・改行を落とす）。
       ★HTMLでは don't が don&#x27;t になる＝unescape しないと必ず不一致（2026-08-24 実測）。"""
    return re.sub(r"[\s\u3000]+", "", _html.unescape(strip_tags(s)))


def extract_questions(html):
    """配信HTMLから (mondai_id, 設問文) を順に取り出す。
       構造＝<section><h2>大問N …</h2> <p class="q"><span class="qn">(k)</span>本文</p> …"""
    out = []
    body = re.split(r'<div class=["\']pagebreak["\']>', html)[0]  # 巻末より前＝問題面
    for sec in re.findall(r"<section>(.*?)</section>", body, re.S):
        m = re.search(r"<h2[^>]*>\s*大問\s*([0-9０-９]+)", sec)
        dm = m.group(1) if m else "?"
        for q in re.findall(r'<p class=["\']q["\']>(.*?)</p>', sec, re.S):
            n = re.search(r'<span class=["\']qn["\']>\((\d+)\)</span>', q)
            kn = n.group(1) if n else "?"
            text = _html.unescape(strip_tags(re.sub(r'<span class=["\']qn["\']>.*?</span>', "", q, flags=re.S)))
            text = re.sub(r"[\s\u3000]+", " ", text).strip()
            out.append((f"大問{dm}({kn})", text))
    return out


def core_terms(q):
    """answer_core を語のリストへ。文字列なら読点・中黒で割る。"""
    v = q.get("answer_core")
    if v is None:
        return None
    if isinstance(v, str):
        v = re.split(r"[、,／/・\s]+", v)
    terms = []
    for t in v:
        t = str(t).strip()
        if len(t) >= MIN_TERM and t not in GENERIC and t.lower().strip(".?!,'’") not in STOP_EN:
            terms.append(t)
    return terms


def core_overlap(text, q):
    """設問文 text に answer_core の中核語が出ていないかを見る共通判定。
       ★配信ゲート（本ファイル main）と承認前の設計シート（build_design_sheet.py）が
         同じ関数を呼ぶ＝両者のドリフト防止（2026-08-25 切り出し）。
       返り値 (未宣言か, 見つかった語のリスト)。"""
    terms = core_terms(q)
    if terms is None:
        return True, []
    return False, [t for t in terms if t in text]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    html = open(sys.argv[1], encoding="utf-8").read()
    d = json.load(open(sys.argv[2], encoding="utf-8"))
    qs = d.get("questions")
    if qs is None:
        print("  [skip] questions 無し＝類題集 or 検査対象外")
        sys.exit(0)

    level = str(d.get("level") or d.get("difficulty") or "")
    hard = any(k in level for k in ("応用", "発展"))
    pairs = extract_questions(html)
    by_id = {q.get("mondai_id"): q for q in qs}

    ng, warn = [], []

    # ── 突合：HTMLの設問とJSONの設問が同じか（JSONだけ整える抜け道を塞ぐ）
    if len(pairs) != len(qs):
        ng.append(f"  ・[突合] HTMLの設問 {len(pairs)}問 ≠ JSONの設問 {len(qs)}問")
    miss_prompt, mismatch = [], []
    for qid, text in pairs:
        q = by_id.get(qid)
        if q is None:
            ng.append(f"  ・[突合] HTMLの {qid} がJSONに無い")
            continue
        p = q.get("prompt")
        if p is None:
            miss_prompt.append(qid)
        elif norm(p) != norm(text):
            mismatch.append(qid)
    if miss_prompt:
        msg = ("  ・[突合] prompt（設問文）が未記載: " + " ".join(miss_prompt[:20])
               + "  ＝JSONに設問文を必須化（無いとHTMLとの突合ができない）")
        (ng if hard else warn).append(msg)
    if mismatch:
        ng.append("  ・[突合] JSONの prompt とHTMLの設問文が不一致: " + " ".join(mismatch[:20]))

    # ── 本体の4検査
    n_view = n_count = n_core = n_declared = 0
    for qid, text in pairs:
        q = by_id.get(qid) or {}
        reason = str(q.get("hint_reason") or "").strip()
        if reason:
            n_declared += 1

        hits = [lab for pat, lab in VIEWPOINT_RULES if re.search(pat, text)]
        if hits:
            n_view += 1
            line = f"  ・{qid}：〔1〕観点の手渡し（{'／'.join(hits[:3])}）"
            if reason:
                warn.append(line + f"  ※申告あり: {reason[:40]}")
            else:
                (ng if hard else warn).append(line + "  ＝hint_reason の宣言が無い")

        if any(re.search(p, text) for p in COUNT_PATTERNS):
            n_count += 1
            line = f"  ・{qid}：〔3〕個数の先出し（区分数を教えている）"
            if reason:
                warn.append(line + f"  ※申告あり: {reason[:40]}")
            else:
                (ng if hard else warn).append(line + "  ＝hint_reason の宣言が無い")

        undeclared_core, found = core_overlap(text, q)
        if undeclared_core:
            if hard:
                ng.append(f"  ・{qid}：answer_core（採点の合格条件となる語）が未宣言"
                          "＝一意性は設問でなく解答側に持たせること")
        else:
            if found:
                n_core += 1
                # 宣言があっても通さない（答えそのものを渡しているため）
                ng.append(f"  ・{qid}：〔2〕答えの中核語が設問文にある → {' '.join(found[:5])}"
                          "  ＝宣言があっても不可")

    print(f"  設問 {len(pairs)}問 / 観点の手渡し {n_view}件 / 個数の先出し {n_count}件 / "
          f"答えの中核語の重なり {n_core}件 / hint_reason 宣言 {n_declared}件")
    for line in warn[:40]:
        print("  ⚠" + line[3:] if line.startswith("  ・") else line)
    if ng:
        print(f"  [NG] ヒント検査に {len(ng)}件（level={level or '未宣言'}）")
        for line in ng[:40]:
            print(line)
        print("       観点は設問に足さず、一意性は answer_core（解答側）で担保すること。"
              "どうしても足すなら hint_reason を宣言する（黙って足さない）。")
        sys.exit(1)
    print(f"  [OK] 設問文の検査を通過（level={level or '未宣言'}／観点の手渡し {n_view}件・"
          f"個数の先出し {n_count}件はすべて hint_reason 申告あり／中核語の重なり 0件）")
    sys.exit(0)


if __name__ == "__main__":
    main()
