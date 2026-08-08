"""ワーク写真を読み取り可能なサイズに前処理する（quiz-generator / mock-test-generator 共通）。

安全フックが1ファイル100KB超の読み込みをブロックするため、そのままでは
スマホで撮った見開き写真（4〜5MB）を読めない。
見開きを左右のページに割り、さらに上下に割って、1ファイルを98KB未満に収める。

**カラーのまま扱う**（2026-08-08 実測）。
グレースケールにすると赤い手書きの印が印刷の線と区別できなくなる。
しかも実測ではカラー79KB＜グレー95KB で、色を捨てても小さくならない
（JPEGは色差成分を元から強く間引くため）。

**向きは機械で決めない。** スマホの見開き写真はEXIFでは直らないことが多く、
縦長＝本が横倒し（反時計90度）、横長＝上下逆さま（180度）など撮り方でばらつく。
先に --thumb で縮小版を出し、目で見て向きを決めてから本処理にかける。

使い方:
    # ① 向きの確認用サムネイル（1枚ずつ小さく出す）
    python prep_images.py --thumb <出力フォルダ> <画像1> [画像2 ...]

    # ② 本処理（画像ごとに 回転／ページ番号 を指定できる）
    python prep_images.py <出力フォルダ> <画像1>[@回転][=ページ] ...

    例) python prep_images.py out A.jpg@90=p18-19 B.jpg@180=p20-21 C.jpg

回転は 0 / 90（反時計） / 180 / 270。省略時は 0。
ページは p18-19（見開き）／p18（単ページ）。省略時は img01 のような仮名になり、
    そのあと中身を読んでページ番号を確定し、リネームする。

出力: <出力フォルダ>/<ページ>a.jpg（上半分）／<ページ>b.jpg（下半分）
"""
import os
import re
import sys

from PIL import Image, ImageOps

LIMIT = 98_000          # フックの上限100KBに対する安全域
LONG_EDGE = 1500        # 1ページあたりの長辺。これ以下だと小さい文字が潰れる
OVERLAP = 40            # 上下に割るときの重なり。境界の行が消えるのを防ぐ
THUMB_EDGE = 900        # サムネイルの長辺（向きが分かれば足りる）

ROTATE = {90: Image.ROTATE_90, 180: Image.ROTATE_180, 270: Image.ROTATE_270}


def parse_arg(arg):
    """'A.jpg@90=p18-19' を (パス, 回転, ページラベル) に分解する"""
    path, rot, labels = arg, 0, None
    if '=' in path:
        path, spec = path.rsplit('=', 1)
        labels = page_labels(spec)
    if '@' in path:
        path, r = path.rsplit('@', 1)
        rot = int(r) % 360
        if rot not in (0, 90, 180, 270):
            raise SystemExit(f'回転は 0/90/180/270 のいずれか: {arg}')
    return path, rot, labels


def page_labels(spec):
    """'p18-19' → ['p18','p19'] / 'p18' → ['p18'] / 取れなければ None"""
    m = re.search(r'p?(\d+)\s*-\s*p?(\d+)', spec)
    if m:
        return [f'p{m.group(1)}', f'p{m.group(2)}']
    m = re.search(r'p?(\d+)', spec)
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


def load(path, rot):
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    if rot:
        im = im.transpose(ROTATE[rot])
    return im


def make_thumb(path, outdir, idx):
    im = load(path, 0)
    w, h = im.size                       # EXIF補正後のサイズで向きを言う
    im.thumbnail((THUMB_EDGE, THUMB_EDGE), Image.LANCZOS)
    out = os.path.join(outdir, f'thumb{idx:02d}.jpg')
    q, size = save_within_limit(im, out)
    shape = '縦長' if h > w else '横長'
    return out, q, size, f'{w}x{h} {shape}', os.path.basename(path)


def process(path, outdir, rot, labels, idx):
    im = load(path, rot)
    w, h = im.size
    if labels is None:
        # ページ番号が未確定。仮名で出し、あとで中身を読んで確定・リネームする。
        labels = [f'img{idx:02d}L', f'img{idx:02d}R'] if w > h * 1.2 else [f'img{idx:02d}']
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
    args = sys.argv[1:]
    thumb = False
    if args and args[0] == '--thumb':
        thumb, args = True, args[1:]
    if len(args) < 2:
        raise SystemExit(__doc__)
    outdir, items = args[0], args[1:]
    os.makedirs(outdir, exist_ok=True)

    if thumb:
        for i, a in enumerate(items, 1):
            out, q, size, shape, src = make_thumb(a, outdir, i)
            print(f'{os.path.basename(out)}: {shape}  ← {src}')
        print('\n→ サムネイルを見て向きを決め、本処理で @90 / @180 を指定すること')
        return

    for i, a in enumerate(items, 1):
        path, rot, labels = parse_arg(a)
        for out, q, size in process(path, outdir, rot, labels, i):
            # q=32 でもワークの本文・穴埋め番号は判読できることを実機で確認済み（2026-08-08）。
            # 下限まで落ちたものだけ念のため知らせる。
            warn = '  ※圧縮の下限。判読を確認すること' if q <= 32 else ''
            print(f'{os.path.basename(out)}: q={q} {size/1024:.0f}KB{warn}')


if __name__ == '__main__':
    main()
