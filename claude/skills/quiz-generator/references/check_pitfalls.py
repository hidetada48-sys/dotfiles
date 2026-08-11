"""つまずき（よくある誤り）が問題集・模試に織り込まれているかを機械で検査する。

2026-08-11 新設。背景＝2026-08-10 の skill 改修で
「関連問題／模試のコア項目は、単元のつまずき（落とし穴）を突く設計にし、
 巻末（解説）に『▶よくある誤り』を書く」を全教科の作法にした。
ところが文章の但し書きだけで、実際には反映を飛ばせてしまった（2026-08-11 理科で発生）。
そこで「タグと解説が無ければ配布できない」機械の関門にする。

**数学とその他で作り方が違う（skill が2系統に分かれている）ので、ここも分岐する：**
  - その他教科（理・社・国・英 等）＝関連問題が「別角度＋つまずき」。
        → 各「関連」に pitfall タグが要る。
  - 数学＝段階上げ（類似1→類似2→類似3）。
        → 各「類似2」「類似3」に pitfall タグが要り、
          さらに key_point が土台（類似1）と別（一段上がっている）こと
          ＝同一なら「問い方替え」＝失敗（2026-08-10 の指摘）。

検査対象は2種類の JSON を自動判別する：
  - 問題集（quiz-generator）の log.json … "problems": [...]
  - 模試（mock-test-generator）の 出題履歴.json … "questions": [...]

使い方:
    python check_pitfalls.py <html> <log_or_history.json>

判定:
  ① JSON 側：対象の各問に pitfall（狙うつまずき）が入っているか。
     空欄・キー無しは失敗。「なし（知識確認）」等の明示は可（＝考えた上での除外）。
  ② HTML 側：解説に「▶よくある誤り」が、実際に罠を狙う問題の数だけあるか。
  どちらか欠けたら終了コード1（＝そのまま配布してはいけない）。
"""
import json
import re
import sys

# pitfall 欄に入っていても「罠なし」とみなし、HTML の▶よくある誤りを要求しない表現。
# （純粋な知識確認など。ただしキー自体は必須＝黙って省けない。）
NO_TRAP = re.compile(r'^\s*(なし|無し|none|-|―|特になし)', re.IGNORECASE)
MARK = '▶よくある誤り'


def is_math(subject):
    return subject and ('数学' in subject or 'math' in subject.lower())


def norm(s):
    return re.sub(r'\s+', '', str(s or '')).lower()


def pitfall_of(p):
    """問題オブジェクトから pitfall 文字列を取り出す（表記ゆれ吸収）。無ければ None。"""
    for k in ('pitfall', '狙うつまずき', 'tsumazuki', 'つまずき'):
        if k in p and str(p[k]).strip():
            return str(p[k]).strip()
        if k in p:            # キーはあるが空
            return ''
    return None


def has_trap(pf):
    """pitfall 文字列が『実際に罠を狙う』ものか（＝HTMLに▶が要るか）。"""
    return bool(pf) and not NO_TRAP.match(pf)


def targets_quiz(problems, subject):
    """検査対象の問題（type で選ぶ）を (対象リスト, ラベル) で返す。"""
    def typ(p):
        return norm(p.get('type'))
    if is_math(subject):
        # 段階上げ＝類似2・類似3（関連が残っていれば併せて見る）
        tgt = [p for p in problems if typ(p) in ('類似2', '類似3') or '関連' in typ(p)]
        return tgt, '数学：類似2/類似3'
    # その他＝関連
    tgt = [p for p in problems if '関連' in typ(p)]
    return tgt, 'その他：関連'


def check_math_keypoint(problems):
    """数学：同一 source 内で 類似2/3 の key_point が土台（類似1）と別か。"""
    bysrc = {}
    for p in problems:
        bysrc.setdefault(p.get('source', ''), []).append(p)
    bad = []
    for src, ps in bysrc.items():
        base = next((p for p in ps if norm(p.get('type')) in ('類似', '類似1')), None)
        if not base:
            continue
        bk = norm(base.get('key_point'))
        for p in ps:
            if norm(p.get('type')) in ('類似2', '類似3') and norm(p.get('key_point')) == bk and bk:
                bad.append((src, p.get('type')))
    return bad


def check(html_path, json_path):
    doc = json.load(open(json_path, encoding='utf-8'))
    subject = doc.get('subject', '')
    html = open(html_path, encoding='utf-8').read()
    ng = 0

    if 'problems' in doc:
        kind = '問題集(quiz)'
        targets, label = targets_quiz(doc['problems'], subject)
    elif 'questions' in doc:
        kind = '模試(mock)'
        # 模試は全コア項目に《狙うつまずき》を併記する運び（無ければ「なし」明示）。
        targets, label = doc['questions'], '模試：全コア項目'
    else:
        print('[NG] JSON に "problems" も "questions" も無い。'
              '問題集の log.json か模試の出題履歴JSONを渡すこと。')
        return 1

    print(f'種別: {kind} / 教科: {subject or "不明"} / 検査対象: {label}（{len(targets)}件）')
    print('-' * 60)

    if not targets:
        print('[NG] つまずきを狙う対象問題が0件。関連問題（数学は類似2/3）が'
              '設計に入っていない疑い。SKILL ステップ4のつまずき駆動を満たすこと。')
        return 1

    # ① JSON 側：pitfall タグの有無
    trap_count = 0
    for p in targets:
        pf = pitfall_of(p)
        who = f'{p.get("source") or p.get("mondai_id") or p.get("core_item") or "?"}' \
              f'（{p.get("type") or p.get("format") or ""}）'
        if pf is None:
            ng += 1
            print(f'[欠落] {who} … pitfall（狙うつまずき）欄が無い。'
                  '罠が無いなら "なし（知識確認）" と明示すること')
        elif pf == '':
            ng += 1
            print(f'[空欄] {who} … pitfall が空。狙う誤りを書くか "なし（…）" と明示')
        elif has_trap(pf):
            trap_count += 1
            print(f'[OK]   {who} … 狙うつまずき「{pf}」')
        else:
            print(f'[除外] {who} … つまずき無しと明示（{pf}）＝HTMLの▶は不要')

    # 数学の key_point 上げ確認
    if 'problems' in doc and is_math(subject):
        bad = check_math_keypoint(doc['problems'])
        for src, t in bad:
            ng += 1
            print(f'[同一] {src}（{t}）… key_point が類似1と同じ＝'
                  '「問い方替え」。段階を一段上げること（数の複雑化/手数増/複合）')

    # ② HTML 側：▶よくある誤り の本数
    marks = html.count(MARK)
    print('-' * 60)
    print(f'HTML の「{MARK}」… {marks}本 / 罠を狙う問題 {trap_count}件')
    if marks < trap_count:
        ng += 1
        print(f'[不足] 巻末の解説に「{MARK}」が {trap_count} 本必要（罠ごとに1行）。'
              f'現状 {marks} 本。解説を追記すること')

    print('-' * 60)
    if ng:
        print(f'[NG] つまずきの反映に {ng} 件の不備。'
              '直して JSON と HTML を作り直すまで配布してはいけない。')
        return 1
    print('[OK] つまずき（狙う誤り＋▶よくある誤り）が反映されている。')
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(check(sys.argv[1], sys.argv[2]))
