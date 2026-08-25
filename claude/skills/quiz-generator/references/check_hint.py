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

# ★第7次改修（2026-08-25）＝設問文の「長さ」と「手順の誘導」を見る。
#   背景＝第4次で設問文を読むようにしたが、見ていたのは決まった4つの型だけだった。
#   専務に差し戻された31問を後から掛け直すと 0件で素通り（指示の平均72字・最長148字）。
#   語を足すモグラ叩きでは次の言い回しで抜けるので、**語に依存しない指標＝長さ**を主にする。
#   実データの分離（理科ver3 第1版=差し戻し / 第2版=承認）：
#     指示55字超 … 第1版 24件 / 第2版 0件      読点3個以上 … 第1版 7件 / 第2版 0件
# 〔5〕手順を誘導する表現（「〜を求め、〜し、〜を書きなさい」の複合指示・観点の指定）。
PROCEDURE_RULES = [
    (r"を求め[、，]", "「〜を求め、」＝解く手順を指定している"),
    (r"がわかるように|が分かるように", "「〜がわかるように」＝答え方を指定している"),
    (r"もあわせて|も併せて", "「〜もあわせて」＝複合指示"),
    (r"それぞれについて", "「それぞれについて」＝観点を割り振っている"),
    (r"をもとに|を基に", "「〜をもとに」＝使う材料を指定している"),
    (r"をふまえて|を踏まえて", "「〜をふまえて」＝観点の指定"),
    (r"決め手(?:になる|となる)(?:特徴|観点|点)を", "「決め手になる特徴を」＝観点を渡している"),
    (r"からだのつくりの(?:ちがい|違い)", "「からだのつくりの」＝見る観点を渡している"),
    # ★個数の指定は「2つ以上」だけを弾く（2026-08-25 判断）。
    #   「2つあげなさい」＝“2つある”と教える＝1つしか思いつかない生徒に残りの存在を渡すヒント。
    #   「1つ書きなさい」＝答えの分量の指定にすぎず、中身は渡していない（採点の公平にも要る）。
    (r"[2-9２-９二三四五六七八九]\s*つ(?:以上)?(?:あげ|挙げ|答え|書き|述べ)", "個数の指定＝“何個ある”を教えている"),
]

# 〔6〕設問文の長さ。データ（数値・単位・記号）を除いた「指示のことば」で測る。
LEN_WARN = 45      # これを超えたら注意（読み手が趣旨を取りにくい）
LEN_NG = 55        # 応用はこれを超えたら配信拒否（誘導が紛れ込む余地が大きい）
COMMA_NG = 3       # 読点がこの数以上＝複合指示の疑い

# ★第8次改修（2026-08-25 専務指摘）＝process 軸（社会・国語）は設問文をもっと短く縛る。
#   complexity 軸（数学・理科計算・英語）は測定値や条件を設問に載せる必要があるので 55字でよい。
#   process 軸には載せるデータが無い。長くなるのは条件・観点・答えの目次を足したときだけである。
#   歴史ver3 で「〜を示して説明」「〜をあげて説明」が全部素通りし、点検0件のまま易しい問題が
#   できた（＝設問が答えの見取り図になっていた）ので、専用の上限と付帯指示句の禁止を置く。
LEN_NG_PROCESS = 35     # process軸の応用はこれを超えたら配信拒否
COMMA_NG_PROCESS = 2    # process軸の応用は読点がこの数以上でNG（＝1文1問い）

# 〔7〕付帯指示句＝「答えに何を書けばよいか」の目次を設問側が渡してしまうもの。
ATTACH_RULES = [
    (r"を示して", "「〜を示して」＝答えに書く要素を渡している"),
    (r"を(?:あげ|挙げ)て(?:説明|述べ|答え)", "「〜をあげて」＝答えに書く要素を渡している"),
    (r"を答え[、，][^。]*(?:説明|述べ)", "「〜を答え、…説明」＝答えの目次を割り振っている"),
    (r"名(?:と|を)[^。]*(?:ちがい|違い)を", "「名と…ちがいを」＝答えの構成を割り振っている"),
    (r"(?:背景|理由|目的)と[^。]*(?:を|も)(?:説明|答え)", "「背景と〜」＝答えを2枠に割っている"),
]

_DATA_RE = re.compile(r"[0-9０-９A-Za-zＡ-Ｚａ-ｚ．.,／/×÷＝=・（）()【】〜~°³²]+")


def instruction_len(text):
    """設問文から数値・単位・記号を落とした「指示のことば」の文字数。
       ★データが長いだけの問い（測定値を並べる計算問題）を誤って弾かないため。"""
    return len(_DATA_RE.sub("", text))


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
    # ★第8次：process軸（社会・国語）の応用は設問文の上限を厳しくする
    axis = str(d.get("difficulty_primary") or "")
    is_process = ("process" in axis) or ("思考" in axis) or ("種類" in axis)
    len_ng = LEN_NG_PROCESS if (is_process and hard) else LEN_NG
    comma_ng = COMMA_NG_PROCESS if (is_process and hard) else COMMA_NG
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
    n_proc = n_long = n_attach = 0
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

        # 〔5〕手順の誘導（第7次改修）
        phits = [lab for pat, lab in PROCEDURE_RULES if re.search(pat, text)]
        if phits:
            n_proc += 1
            line = f"  ・{qid}：〔5〕手順の誘導（{phits[0]}）"
            (ng if hard else warn).append(line)

        # 〔6〕設問文が長い（第7次改修・語に依存しない指標）
        # 〔7〕付帯指示句（第8次改修）＝答えの目次を渡していないか
        ahits = [lab for pat, lab in ATTACH_RULES if re.search(pat, text)]
        if ahits:
            n_attach += 1
            (ng if hard else warn).append(
                f"  ・{qid}：〔7〕付帯指示句（{ahits[0]}）＝素で問うこと")

        ilen, ncomma = instruction_len(text), text.count("、")
        if ilen > len_ng or ncomma >= comma_ng:
            n_long += 1
            why = (f"指示{ilen}字＞{len_ng}" if ilen > len_ng else f"読点{ncomma}個")
            (ng if hard else warn).append(
                f"  ・{qid}：〔6〕設問文が長い（{why}）＝1問1指示に分け、"
                "条件・数値はリード文へ出すこと")
        elif ilen > LEN_WARN:
            warn.append(f"  ・{qid}：〔6〕設問文がやや長い（指示{ilen}字）")

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

    ilens = [instruction_len(t) for _, t in pairs] or [0]
    print(f"  設問 {len(pairs)}問 / 観点の手渡し {n_view}件 / 個数の先出し {n_count}件 / "
          f"答えの中核語の重なり {n_core}件 / hint_reason 宣言 {n_declared}件")
    print(f"  手順の誘導 {n_proc}件 / 付帯指示句 {n_attach}件 / 長すぎる設問文 {n_long}件 / "
          f"指示のことば 平均{sum(ilens)//len(ilens)}字・最長{max(ilens)}字"
          f"（注意{LEN_WARN}字・不可{len_ng}字）")
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
          f"個数の先出し {n_count}件はすべて hint_reason 申告あり／中核語の重なり 0件／"
          f"手順の誘導 0件・長すぎる設問文 0件）")
    sys.exit(0)


if __name__ == "__main__":
    main()
