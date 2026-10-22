#!/usr/bin/env python3
"""html-gate.sh の判定部。Stopフックの入力JSONを標準入力で受け取り、
"block\t<キー>" または "skip\t" を1行出力する。

判定：直前の回答が「長い」のにレポートURLが無ければ block。
　　　長さは **行数（空行除く）と 文字数（空白・改行除く）のどちらか** で測る。
例外：コードブロックを含む／直近の専務の指示が「チャットで」等／URLあり。

★2026-09-02 修正：
  Stopフックの入力JSONには last_assistant_message が含まれない場合がある
  （含まれない環境では判定対象が空＝常にskipになり、関門が一度も鳴らなかった）。
  そのため transcript_path から直近のassistant発話を読む経路を追加した。
"""
import json
import re
import os
import sys

LIMIT = int(os.environ.get("HTML_GATE_LIMIT", "10"))
# ★2026-09-13 追加：行数だけで見ていたため「長い段落を数行」だと素通りしていた
#   （6段落＝6行でも中身は800字、という回答が実際に抜けた＝専務指摘）。
#   文字数でも測る。空白・改行は数えない。
#   ★2026-10-01 専務指示：400字 → 300字
CHAR_LIMIT = int(os.environ.get("HTML_GATE_CHAR_LIMIT", "300"))
# 専務が「チャットで答えろ」と明示した場合は鳴らさない
# ★2026-09-23 追加（専務指示・恒久）：レポートを作ったのにチャットで中身をだらだら書いていた。
#   リンクがあれば無条件合格だった抜け道を塞ぐ。リンクがある回答は、URL部分を除いて
#   行数5・文字数250まで（＝結論1行＋リンク＋判断を仰ぐこと1〜3行）。
# ★2026-09-24 強化（専務指示）：5行・250字では結論行・伺い行にレポートの数字や直し方を書き写しても通っていた。
#   リンクがある回答は 結論1行・リンク1行・伺い1行＝URLを除き 行数3・文字数120 まで。
# ★2026-10-05 専務指示で廃止：リンク付きも同じ基準（URLを除き10行・300字）。参照する所のために値だけ残す
LINK_LINE_LIMIT = LIMIT
LINK_CHAR_LIMIT = CHAR_LIMIT


def body_size(msg):
    """URLを除いた本文の行数・文字数を返す（リンクの長さで鳴らさないため）"""
    t = re.sub(r"\(https?://[^)\s]*\)", "", msg)
    t = re.sub(r"https?://\S+", "", t)
    lines = [l for l in t.split("\n") if l.strip()]
    return len(lines), len("".join(t.split()))


# ★2026-10-04 専務指示「4行ルールを直せ」：4行以内は測らずに出してよいと読まれ、4行・317字が測られずに出た。
#   0＝行数によらず、測った下書きと同じ文でない返答はすべて違反として記録する
PRECHECK_MIN_LINES = int(os.environ.get("HTML_GATE_PRECHECK_MIN_LINES", "0"))
PRECHECK_LOG = os.path.join(os.path.expanduser("~"), ".claude", "state", "precheck_ok.txt")


def norm_hash(msg):
    """空白・改行を除いた本文の指紋（下書きと表示した回答が同じ文かを見る）"""
    import hashlib
    return hashlib.sha1("".join(msg.split()).encode("utf-8")).hexdigest()


def prechecked(msg):
    """precheck-answer.py が OK を出した下書きの指紋に、この回答が含まれるか"""
    try:
        with open(PRECHECK_LOG, encoding="utf-8") as f:
            return norm_hash(msg) in {l.split("\t")[0] for l in f if l.strip()}
    except Exception:
        return False


# ★2026-10-05 専務指示：2行以上 → 5行以上
BULLET_LIMIT = int(os.environ.get("HTML_GATE_BULLET_LIMIT", "5"))
BULLET_RE = re.compile(r"^\s*(?:[・\-\*•●○▶]\s*|\d{1,2}[\.\)．）]\s*|〔\d{1,2}〕|[①-⑳]|[(（]\d{1,2}[)）])")


# 行の途中に並べた番号（「直し方：〔1〕…〔2〕…」）も一覧として数える（2026-10-01 専務叱責：1行に詰めて一覧の見張りをすり抜けた）
# ただし数えるのは、番号が1から順に並び（1・2・3…）、番号と番号の間の中身が平均 INLINE_SEG_MIN 字以上のときだけ
# （2026-10-01 専務承認＝案B。「②リール明細・⑥リール」のシート名や「①コミット ②プッシュ ③記憶」の呼び名を一覧と数えていた）
INLINE_ENUM_RE = re.compile(r"〔(\d{1,2})〕|([①-⑳])|[(（](\d{1,2})[)）]")
INLINE_SEG_MIN = int(os.environ.get("HTML_GATE_INLINE_SEG_MIN", "15"))


def _enum_no(m):
    """番号の印から数を取り出す（〔3〕→3・③→3・(3)→3）"""
    if m.group(1):
        return int(m.group(1))
    if m.group(2):
        return ord(m.group(2)) - ord("①") + 1
    return int(m.group(3))


def inline_items(line):
    """行の途中に1から順に並んだ番号の項目数（中身が短い呼び名の並びは0）"""
    ms = list(INLINE_ENUM_RE.finditer(line))
    ks = [_enum_no(m) for m in ms]
    best, run, start = None, 0, None
    for i, k in enumerate(ks):
        if k == 1:
            run, start = 1, i
        elif start is not None and k == run + 1:
            run += 1
        if run >= 2:
            best = (start, start + run - 1)
    if not best:
        return 0
    a, b = best
    segs = [ms[i + 1].start() - ms[i].end() for i in range(a, b)] + [min(len(line) - ms[b].end(), 60)]
    return b - a + 1 if sum(segs) / len(segs) >= INLINE_SEG_MIN else 0


def bullet_lines(msg):
    """箇条書きの行（・／-／1. ／〔1〕／①／(1) で始まる行）の数。表の行（| で始まる）も一覧として数える。
    行の途中に1から順に番号を並べた行は、その番号の数だけ一覧の項目として数える"""
    n = 0
    for l in msg.split("\n"):
        if not l.strip():
            continue
        inline = inline_items(l)
        if inline:
            n += inline
        elif BULLET_RE.match(l) or l.lstrip().startswith("|"):
            n += 1
    return n


def digit_lines(msg):
    """リンク（8830/8831）を含まない行のうち、数字（半角・全角）を含む行の数"""
    n = 0
    for l in msg.split("\n"):
        if not l.strip() or has_link(l):
            continue
        if re.search(r"[0-9０-９]", l):
            n += 1
    return n


def has_link(msg):
    return "127.0.0.1:8830" in msg or "127.0.0.1:8831/open" in msg


SKIP_WORDS = ("チャットで", "HTML不要", "htmlは要らない", "そのまま書", "口頭で", "短く")


def out(verdict, key=""):
    sys.stdout.write(verdict + "\t" + key + "\n")
    sys.exit(0)


def _text_of(content):
    """message.content（文字列 or ブロック配列）からテキストだけ取り出す"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            b.get("text", "") for b in content
            if isinstance(b, dict) and b.get("type", "text") == "text"
        )
    return ""


def scan_transcript(path):
    """トランスクリプトを1回走査し、(直近のユーザー発話, 直近のassistant発話) を返す"""
    return scan_transcript3(path)[:2]


def scan_transcript3(path):
    """トランスクリプトを1回走査し、(直近のユーザー発話, 直近のassistant発話, 直近の専務の依頼) を返す。
    直近の専務の依頼＝フックの差し戻し（Stop hook feedback）とスキルの本文などの裏の発話を除いた、最後のユーザー発話"""
    if not path or not os.path.exists(path):
        return "", "", ""
    user_text, asst_text, prompt = "", "", ""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                t = e.get("type")
                if t not in ("user", "assistant"):
                    continue
                s = _text_of(e.get("message", {}).get("content", "")).strip()
                if not s:
                    continue
                if t == "user":
                    user_text = s
                    if not e.get("isMeta") and not s.startswith("Stop hook feedback"):
                        prompt = s
                else:
                    asst_text = s
    except Exception:
        return user_text, asst_text, prompt
    return user_text, asst_text, prompt


# ★2026-10-20 専務決定（控え帳 mvfayel44u8d・mvfsy0zb0iny）：測らなくてよい返答。
#   正典＝mino-sakura-hq docs/plans/2026-10-20-測らなくてよい返答の設計.md
#   種類A＝保存3点の報告／朝の取り込みの報告／保存の差し戻し後の報告。出す前の確認も、ここでの記録も一切しない。
#   種類B＝種類A以外で、URLと改行・空白を除き150字以内、最後の行が伺いで終わらない返答。試しに種類Aと同じく一切しない
#   （だめなら、出す前の1〜4＝中身の書き出し・長さ・呼び名・リンクだけ行う形に改める＝同日 専務決定）
SAVE_BUTTON = "今日の作業をコミット・プッシュ・記憶まで保存して。"   # 操作盤の〔保存3点〕ボタンが送る文
SHORT_LIMIT = int(os.environ.get("HTML_GATE_SHORT_LIMIT", "150"))
ASK_END_RE = re.compile(r"(？|\?|ください。?|よろしいですか。?|伺います。?|お願いします。?)\s*$")


def is_save_request(prompt):
    """専務の依頼が保存3点（ボタンの文、または「保存」と「コミット・プッシュ・記憶」のどれかを含む依頼）か"""
    p = prompt.strip()
    if p == SAVE_BUTTON:
        return True
    return "保存" in p and any(w in p for w in ("コミット", "プッシュ", "記憶"))


def exempt_kind(msg, last_user, prompt):
    """測らなくてよい返答なら種類（"A保存"・"A朝"・"A差し戻し"・"B短い"）を、そうでなければ "" を返す"""
    first = next((l.strip() for l in msg.split("\n") if l.strip()), "")
    if first.startswith("最新の取り込み："):
        return "A朝"
    if last_user.startswith("Stop hook feedback") and "[保存3点セット]" in last_user:
        return "A差し戻し"
    if is_save_request(prompt):
        return "A保存"
    last = next((l.strip() for l in reversed(msg.split("\n")) if l.strip()), "")
    if body_size(msg)[1] <= SHORT_LIMIT and not ASK_END_RE.search(last):
        return "B短い"
    return ""


# ★2026-10-22 専務承認（控え帳2「独自の言葉」の直し方3）：種類Bの短い返答は出す前の点検をしないため、
#   専務に通じない言葉の一覧（jargon_words.txt）にも掛かっていなかった（10/21「定期で作る物」が素通り）。
#   種類Bにだけ一覧を掛け、当たれば違反として記録する（AIは使わない＝待ち時間なし。止めはしない）。
JARGON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jargon_words.txt")
STATE_DIR = os.environ.get("HTML_GATE_STATE_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "state")


def jargon_hits(msg):
    """一覧の言葉が、言い換え（＝）の無い行に出ていれば その言葉の並びを返す（precheck-answer.py と同じ見方）"""
    try:
        with open(JARGON, encoding="utf-8") as f:
            words = [w.strip() for w in f if w.strip() and not w.lstrip().startswith("#")]
    except Exception:
        return []
    hits = []
    for line in msg.splitlines():
        if "＝" in line:
            continue
        body = re.sub(r"\(https?://[^)]*\)|`[^`]*`", "", line)   # URL とファイル名（`…`）は見ない
        hits += [w for w in words if w in body and w not in hits]
    return hits


def record_jargon(msg, hits):
    """短い返答に一覧の言葉が出たことを、次の指示で届く記録と、消さない記録の両方に書く"""
    import datetime
    rec = "\t".join([datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                     "短い返答に専務に通じない言葉（" + "・".join(hits) + "）。言い換えるか「＝○○のこと」を添える",
                     msg.replace("\n", " ")[:60]]) + "\n"
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        for name in ("html-gate_pending.log", "html-gate_violations.log"):
            with open(os.path.join(STATE_DIR, name), "a", encoding="utf-8") as f:
                f.write(rec)
    except Exception:
        pass


def main():
    try:
        d = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))   # UTF-8で読む（既定のcp932だと日本語が約1.65倍に数えられ、短い回答まで止めていた 2026-09-18）
    except Exception:
        out("skip")

    lu, last_asst, prompt = scan_transcript3(d.get("transcript_path") or "")

    msg = d.get("last_assistant_message") or ""
    if isinstance(msg, list):  # 配列形式にも一応対応
        msg = _text_of(msg)
    if not msg.strip():        # フックが渡してくれない環境＝トランスクリプトから拾う
        msg = last_asst
    if not msg.strip():
        out("skip")
    if "```" in msg:              # コード提示は対象外
        out("skip")
    key = str(d.get("prompt_id") or d.get("session_id") or "nokey")[:64]
    if any(kw in lu for kw in SKIP_WORDS):
        out("skip")
    kind = exempt_kind(msg, lu, prompt)
    if kind:   # 測らなくてよい返答（2026-10-20 専務決定）は長さを記録しない
        hits = jargon_hits(msg) if kind == "B短い" else []
        if hits:   # 種類Bだけ、一覧の言葉は記録する（2026-10-22）
            record_jargon(msg, hits)
            out("skip", "J")   # 止めない。2列目の J は試験で見分けるための印
        out("skip")
    # ★2026-10-05 専務指示：リンクの有無で基準を分けない。
    #   旧＝リンク付きの返答だけ「URLを除き3行・120字」。120字では中身が書けず、分かる日本語の点検に落ち続けた
    #   （リンクの無いチャットの方が通りやすく、レポートを避ける方向に流れた）。
    #   新＝どの返答も「空行とURLを除いて10行超 または 300字超」「箇条書き・表の行が5行以上」ならレポートにする。
    # 行数によらず、precheck-answer.py で OK になった下書きと同じ文でなければ違反（2026-09-24／10-04）
    if len([l for l in msg.split("\n") if l.strip()]) > PRECHECK_MIN_LINES and not prechecked(msg):
        sys.stdout.write("block\t" + key + "\tP\n")
        sys.exit(0)
    nb = bullet_lines(msg)
    if nb >= BULLET_LIMIT:
        sys.stdout.write("block\t" + key + "\tB" + str(nb) + "\n")
        sys.exit(0)
    nl, nc = body_size(msg)
    if nl <= LIMIT and nc <= CHAR_LIMIT:
        out("skip")
    # 3列目＝鳴った理由。行数超過なら行数、文字数超過なら「Nc」。リンク付きなら先頭に L
    size = str(nl) if nl > LIMIT else str(nc) + "c"
    sys.stdout.write("block\t" + key + "\t" + ("L" if has_link(msg) else "") + size + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
