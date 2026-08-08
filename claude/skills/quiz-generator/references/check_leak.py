"""問題面に答えが漏れていないかを検査する（quiz-generator / mock-test-generator 共通）。

**生成したら必ず通すこと。** 答えが見えている問題集は問題集ではない。

漏れは3か所から起きる（2026-08-08 に実際に全部やった）：
  ① 出典の見出し … 「◆ p.18 ⑧　亜寒帯の植生　タイガ」のように答えを書いてしまう
  ② 同じ節の別の設問 … 関連問題の文に「タイガが針葉樹ばかりで…」と類似の答えを書く
  ③ 設問文のヒント … 「中心部ではなくどこに」のように選択肢を絞ってしまう
①②は機械で見つかる。③は目で読む。

使い方:
    python check_leak.py <問題集HTML>

判定: 巻末（改ページ以降）を切り離し、問題面だけを見る。
      巻末①の答えが問題面に出ていたら漏れとして報告する。
"""
import os
import re
import sys

MIN_LEN = 2          # これより短い答えは偶然の一致が多いので見ない
DESC_HEAD = 12       # 記述の答えは冒頭この文字数だけを照合する


def normalize(a):
    """答えから照合に使う語を取り出す。『タロいも（ヤムいも…でもよい）』→『タロいも』"""
    a = re.sub(r'（.*?）', '', a)
    a = a.split('、')[0].strip('。 　')
    return a


def check(path):
    s = open(path, encoding='utf-8').read()
    # 巻末（最初の改ページ以降）を落とす
    front = s.split('<div class="pagebreak">')[0]
    answers = re.findall(r'<p class="ansrow"><b>(.+?)：</b> (.+?)</p>', s)

    # 問題面をセクションごとに分ける
    secs = re.findall(r'<section>(.*?)</section>', front, re.S)
    heads = re.findall(r'<h2>(.*?)</h2>', front, re.S)

    leaks = []
    for label, raw in answers:
        key = normalize(raw)
        if len(key) < MIN_LEN:
            continue
        needle = key if len(key) <= DESC_HEAD * 2 else key[:DESC_HEAD]
        for i, sec in enumerate(secs):
            if needle in sec:
                where = '見出し' if (i < len(heads) and needle in heads[i]) else '設問文'
                # 自分の設問文に答えが出るのは、同じ節の別の設問からの漏れ
                leaks.append((label, needle, i + 1, where))
    return answers, secs, leaks


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for path in sys.argv[1:]:
        answers, secs, leaks = check(path)
        print(f'\n=== {os.path.basename(path)} ===')
        print(f'設問 {len(secs)}節 / 答え {len(answers)}件 → 漏れ {len(leaks)}件')
        for label, needle, n, where in leaks:
            print(f'  漏れ: 第{n}節の{where}に「{needle}」'
                  f'（{label} の答え）')
        if leaks:
            print('  → 該当箇所を言い換えて消すこと。'
                  '消せない場合は設問そのものを設計し直す')
        else:
            print('  → 問題面に答えは出ていない')


if __name__ == '__main__':
    main()
