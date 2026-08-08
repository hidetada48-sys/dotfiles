"""ワーク写真を読み取り可能なサイズに前処理する（quiz-generator / mock-test-generator 共通）。

安全フックが1ファイル100KB超の読み込みをブロックするため、そのままでは
スマホで撮った見開き写真（4〜5MB）を読めない。
見開きを左右のページに割り、さらに上下に割って、1ファイルを98KB未満に収める。
文字の判読が目的なのでグレースケールで足りる（色情報を捨てるとサイズが約1/3になる）。

使い方:
    python prep_images.py <出力フォルダ> <画像1> [画像2 ...]

出力: <出力フォルダ>/<元のファイル名の頭>_<ページ>a.jpg / _<ページ>b.jpg
      例) 20260527_213719_p6-7.jpg → p6a.jpg p6b.jpg p7a.jpg p7b.jpg
"""
import os
import re
import sys

from PIL import Image, ImageOps

LIMIT = 98_000          # フックの上限100KBに対する安全域
LONG_EDGE = 1500        # 1ページあたりの長辺。これ以下だと小さい文字が潰れる
OVERLAP = 40            # 上下に割るときの重なり。境界の行が消えるのを防ぐ


def page_labels(path):
    """ファイル名 '..._p6-7.jpg' から ['p6','p7'] を作る。取れなければ None"""
    m = re.search(r'_p(\d+)-(?:p)?(\d+)', os.path.basename(path))
    if m:
        return [f'p{m.group(1)}', f'p{m.group(2)}']
    m = re.search(r'_p(\d+)', os.path.basename(path))
    if m:
        return [f'p{m.group(1)}']
    return None


def save_within_limit(img, out):
    """制限に収まるまで品質を落として保存する"""
    for q in (80, 70, 60, 50, 40, 32):
        img.save(out, 'JPEG', quality=q, optimize=True)
        if os.path.getsize(out) < LIMIT:
            return q, os.path.getsize(out)
    return q, os.path.getsize(out)


def process(path, outdir):
    labels = page_labels(path)
    if not labels:
        raise SystemExit(
            f'ページ番号が読み取れません: {os.path.basename(path)}\n'
            'ファイル名に _p6-7 のようなページ番号が必要です'
            '（workbook-image-process スキルでリネームしてください）'
        )
    im = ImageOps.exif_transpose(Image.open(path)).convert('L')
    w, h = im.size
    if len(labels) == 2:
        boxes = [(0, 0, w // 2, h), (w // 2, 0, w, h)]     # 見開きを左右に割る
    else:
        boxes = [(0, 0, w, h)]
    made = []
    for label, box in zip(labels, boxes):
        page = im.crop(box)
        page.thumbnail((LONG_EDGE, LONG_EDGE), Image.LANCZOS)
        pw, ph = page.size
        halves = (('a', (0, 0, pw, ph // 2 + OVERLAP)),
                  ('b', (0, ph // 2 - OVERLAP, pw, ph)))
        for suffix, hbox in halves:
            out = os.path.join(outdir, f'{label}{suffix}.jpg')
            q, size = save_within_limit(page.crop(hbox), out)
            made.append((out, q, size))
    return made


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    outdir, paths = sys.argv[1], sys.argv[2:]
    os.makedirs(outdir, exist_ok=True)
    for p in paths:
        for out, q, size in process(p, outdir):
            # q=32 でもワークの本文・穴埋め番号は判読できることを実機で確認済み（2026-08-08）。
            # 下限まで落ちたものだけ念のため知らせる。
            warn = '  ※圧縮の下限。判読を確認すること' if q <= 32 else ''
            print(f'{os.path.basename(out)}: q={q} {size/1024:.0f}KB{warn}')


if __name__ == '__main__':
    main()
