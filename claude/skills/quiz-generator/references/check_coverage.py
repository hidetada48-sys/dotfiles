"""模試の材料（log.json）が出題範囲を覆っているかを検査する。

**模擬テストを作る前に必ず通すこと。** 覆っていない材料から作ると、
間違えた箇所だけのテストになる（2026-08-08 に実際にやった）。

模試のコア項目は3軸を同等に評価する：
  ① 視覚的強調（範囲全体のページ）  ② 教科知識  ③ 間違い記録
③は3分の1にすぎない。①は log.json の visual_emphasis が担っており、
**ここが範囲を覆っていなければ、①の軸そのものが欠ける。**

見落としの罠は「数が揃っていると通ってしまう」こと。
pages_scanned が2件・visual_emphasis が2件なら整合はとれているが、
範囲が6見開きなら3分の1しか覆っていない。数の一致では見つからない。

使い方:
    python check_coverage.py <log.json>
    python check_coverage.py <log.json> --range p.18-19,p.20-21,...

判定: log.json の test_range（無ければ --range）を正として、
      pages_scanned と visual_emphasis の両方に載っているかを1ページずつ照合する。
      不足が1件でもあれば終了コード1（＝そのまま模試を作ってはいけない）。
"""
import json
import sys

THIN = 3        # emphasis_points がこれ未満なら読み取りが浅い疑い（絶対の下限）
THIN_RATIO = 0.4  # 他ページの中央値に対してこの割合を下回るページも同じ疑い


def load_range(log, argv):
    """出題範囲を決める。--range が最優先、無ければ test_range。"""
    if '--range' in argv:
        raw = argv[argv.index('--range') + 1]
        return [p.strip() for p in raw.split(',') if p.strip()], '--range'
    if log.get('test_range'):
        return list(log['test_range']), 'test_range'
    return None, None


def check(path, argv):
    log = json.load(open(path, encoding='utf-8'))
    # 模試の出題履歴JSON（questions[]・範囲情報なし）はカバレッジ対象外＝スキップ。
    # ＝run_checks.sh に出題履歴JSONを渡しても誤ってNGにしない（つまずき検査だけ効かせる）。
    # 模試の材料カバレッジは quiz の log.json（visual_emphasis入り）に対して別途通すこと。
    if 'questions' in log and 'visual_emphasis' not in log and 'test_range' not in log \
            and '--range' not in argv:
        print('[skip] これは模試の出題履歴JSON＝カバレッジ検査の対象外。'
              '材料カバレッジは quiz の log.json（visual_emphasis入り）に通すこと。')
        return 0
    rng, src = load_range(log, argv)
    if rng is None:
        print('[NG] 出題範囲が分かりません。')
        print('     log.json に "test_range": ["p.18-19", ...] を入れるか、')
        print('     --range p.18-19,p.20-21 のように渡してください。')
        return 1

    scanned = log.get('pages_scanned') or []
    # visual_emphasis のうち、範囲外と印を付けたものは覆う対象から外す
    ve = {e['page']: e for e in log.get('visual_emphasis', [])
          if not e.get('out_of_range')}

    print(f'出題範囲（{src}）: {len(rng)}件  {" ".join(rng)}')
    print(f'pages_scanned  : {len(scanned)}件  {" ".join(scanned)}')
    print(f'visual_emphasis: {len(ve)}件（範囲外の印が付いたものを除く）')
    print('-' * 60)

    # 「浅いページ」を判定するための基準（覆えているページの中央値）
    counts = sorted(len(ve[p].get('emphasis_points') or []) for p in rng if p in ve)
    med = counts[len(counts) // 2] if counts else 0
    floor = max(THIN, med * THIN_RATIO)

    ng = 0
    thin = []
    for p in rng:
        miss = []
        if p not in scanned:
            miss.append('pages_scanned に無い')
        if p not in ve:
            miss.append('visual_emphasis に無い')
        if miss:
            ng += 1
            print(f'[不足] {p} … {" / ".join(miss)}')
            continue
        n = len(ve[p].get('emphasis_points') or [])
        k = len(ve[p].get('key_sentences') or [])
        # ★空ページはハード[NG]（2026-08-11 強化）。pages_scanned/visual_emphasis に
        #   ページ名を並べただけで中身が無い＝実際に読んでいない状態を通さない。
        if n == 0 and k == 0:
            ng += 1
            print(f'[不足] {p} … visual_emphasis が空（強調0件・見出し0件）'
                  '＝そのページを読んでいない疑い。写真を開いて中身を埋めること')
            continue
        mark = ''
        if n < floor:
            thin.append(p)
            mark = f'  ← 他ページ（中央値{med}件）に比べて少ない。読み落としを疑う'
        print(f'[OK]   {p} … 強調{n}件 / 見出し{k}件{mark}')

    # 範囲に入っていないのに読んであるページ（＝範囲の取り違えの手がかり）
    extra = [p for p in ve if p not in rng]
    if extra:
        print('-' * 60)
        print(f'[参考] 範囲外だが読み取り済み: {" ".join(extra)}')
        print('       範囲の指定が間違っていないか確かめること。')

    print('-' * 60)
    if ng:
        print(f'[NG] {ng}件のページが覆えていません。')
        print('     不足ページの写真を求め、log.json を作り直してから模試に進むこと。')
        return 1
    if thin:
        print(f'[要確認] 全ページ揃っているが、{" ".join(thin)} は強調ポイントが少ない。')
        print('         そのページの写真を開き直し、読み落としが無いか確かめてから進むこと。')
        return 0
    print(f'[OK] 出題範囲{len(rng)}件をすべて覆っています。模試に進んでよい。')
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(check(sys.argv[1], sys.argv[1:]))
