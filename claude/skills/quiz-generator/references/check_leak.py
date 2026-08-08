"""問題面に答えが漏れていないかを検査する（quiz-generator / mock-test-generator 共通）。

**生成したら必ず通すこと。** 答えが見えている問題集は問題集ではない。

漏れは3か所から起きる（2026-08-08 に実際に全部やった）：
  ① 出典の見出し … 「◆ p.18 ⑧　亜寒帯の植生　タイガ」のように答えを書いてしまう
  ② 同じ節の別の設問 … 関連問題の文に「タイガが針葉樹ばかりで…」と類似の答えを書く
  ③ 設問文のヒント … 「中心部ではなくどこに」のように選択肢を絞ってしまう

使い方:
    python check_leak.py <問題集HTML>

終了コード: 見出しへの漏れ（＝最も客観的で重大）が1件でもあれば 1、無ければ 0。
    設問文への語句一致は「注意」として表示するが終了コードには含めない
    （模試は同じ語が選択肢・文脈で頻出し、機械で一律ブロックすると誤検知が多いため。
     設問文のヒントは目で読む＝テンプレの方針どおり）。

対応フォーマット（2026-08-09 頑丈化）:
  - クオートはシングル/ダブルどちらでも可（属性の書き方に依存しない）
  - 巻末① `.ansrow` は2形式に対応
      形式1（quiz-generator）: <p class="ansrow"><b>ラベル：</b> 値</p>
      形式2（模試・グループ）: <p class="ansrow">【n】① 値 ② 値 …</p>
"""
import os
import re
import sys

MIN_LEN = 2          # これより短い答えは偶然の一致が多いので見ない
DESC_HEAD = 12       # 記述の答えは冒頭この文字数だけを照合する
CIRCLED = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'


def strip_tags(x):
    return re.sub(r'<[^>]+>', '', x)


def normalize(a):
    """答えから照合に使う語を取り出す。『タロいも（ヤムいも…でもよい）』→『タロいも』"""
    a = re.sub(r'（.*?）', '', a)
    a = re.sub(r'〔.*?〕', '', a)
    a = a.split('、')[0].strip('。 　:：')
    return a


def extract_answers(s):
    """巻末①から (ラベル, 答え) を取り出す。2形式対応。"""
    # 形式1: <b>ラベル：</b> 値
    fmt1 = re.findall(r'<p class=["\']ansrow["\']><b>(.+?)：</b>\s*(.+?)</p>', s)
    if fmt1:
        return [(l, v) for l, v in fmt1]
    # 形式2: 【n】① 値 ② 値 …（グループ化）
    out = []
    rows = re.findall(r'<p class=["\']ansrow["\']>(.+?)</p>', s, re.S)
    for r in rows:
        t = strip_tags(r).strip()
        m = re.match(r'^(【[^】]*】)', t)
        lab = m.group(1) if m else '【?】'
        body = t[len(lab):] if m else t
        # ①②③… があれば区切る。無ければ全体を1つの答えとして扱う
        parts = re.split(r'[' + CIRCLED + r']', body)
        parts = [p for p in (x.strip('　 :：') for x in parts) if p]
        for p in (parts or [body.strip()]):
            if p:
                out.append((lab, p))
    return out


def check(path):
    s = open(path, encoding='utf-8').read()
    # 巻末（最初の改ページ以降）を落とす（クオート非依存）
    front = re.split(r'<div class=["\']pagebreak["\']>', s)[0]
    answers = extract_answers(s)

    # 問題面をセクション（大問）ごとに分ける。選択肢(.opt)は照合対象から外す
    secs = re.findall(r'<section>(.*?)</section>', front, re.S)
    heads = re.findall(r'<h2[^>]*>(.*?)</h2>', front, re.S)
    secs_wo_opt = [re.sub(r'<p class=["\']opt["\']>.*?</p>', '', x, flags=re.S)
                   for x in secs]

    head_leaks = []   # 見出しへの漏れ（ハード）
    body_leaks = []   # 設問文への語句一致（注意）
    for label, raw in answers:
        key = normalize(raw)
        if len(key) < MIN_LEN:
            continue
        needle = key if len(key) <= DESC_HEAD * 2 else key[:DESC_HEAD]
        for h in heads:
            if needle in strip_tags(h):
                head_leaks.append((label, needle))
                break
        for i, sec in enumerate(secs_wo_opt):
            if needle in strip_tags(sec):
                body_leaks.append((label, needle, i + 1))
    return answers, secs, head_leaks, body_leaks


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    hard_total = 0
    for path in sys.argv[1:]:
        answers, secs, head_leaks, body_leaks = check(path)
        print(f'\n=== {os.path.basename(path)} ===')
        print(f'設問 {len(secs)}節 / 答え {len(answers)}件 '
              f'→ 見出し漏れ {len(head_leaks)}件 / 設問文一致 {len(body_leaks)}件')
        for label, needle in head_leaks:
            print(f'  ⛔ 見出しに「{needle}」（{label} の答え）'
                  '＝見出しには単元名だけにすること')
        for label, needle, n in body_leaks:
            print(f'  ⚠ 第{n}節の設問文に「{needle}」（{label} の答え）'
                  '＝本当に答えを割っていないか目視確認')
        if head_leaks:
            print('  → 見出しの漏れを消すこと（このHTMLは提示不可）')
        elif not body_leaks:
            print('  → 問題面に答えは出ていない')
        else:
            print('  → 見出しの漏れは無し。設問文一致は目視で要確認（頻出語の誤検知の可能性）')
        hard_total += len(head_leaks)
    sys.exit(1 if hard_total else 0)


if __name__ == '__main__':
    main()
