"""ワーク写真から「赤い手書きの印」の候補を絞り込む（quiz-generator 用）。

間違えた問題を赤ペンで印を付けて渡してもらう運用のための道具。
**このスクリプトは答えを出さない。候補を絞るだけ。**

理由：印刷物の赤（見出し・★・国旗・地図の国境線・グラフの折れ線・イラスト）を
機械で完全に除けない。実際に地理のワークで、イギリス国旗・地球儀の矢印・
アメリカの国境線・雨温図の折れ線・ラクダのイラストがすべて引っかかった（2026-08-08）。

そこで役割を3段に分ける：
    ① このスクリプトが候補の位置を出す（見落としを防ぐ）
    ② Claude が該当箇所を切り出して目で見て、手書きか印刷かを判別する
    ③ 読み取った問題番号を本人に読み上げて確認を取る（エコーバック）

使い方:
    python find_redmarks.py <ページ画像1> [画像2 ...]

出力: 画像ごとに候補を「縦N% 横N%（大きさ）」で列挙する。
      Claude はこの座標をもとに該当箇所を切り出して確認する。
"""
import os
import sys

import numpy as np
from PIL import Image

# 赤の判定。r が g・b より十分に強く、かつ暗すぎないこと。
RED_MARGIN = 45
RED_MIN = 90
# 線らしさ。対角の長さがこれ以上で、外接矩形に占める塗りがこれ未満なら「線」。
MIN_DIAG = 22
MAX_FILL = 0.34
# 紙の上にあること。周囲が明るくなければ写真・イラストの中とみなして捨てる。
PAPER_BRIGHT = 185
MARGIN = 12


def label_components(mask):
    """8連結のラベリング（scipy を使わず numpy と Union-Find だけで行う）"""
    h, w = mask.size if isinstance(mask, Image.Image) else mask.shape
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    labels = np.zeros((h, w), dtype=np.int32)
    nxt = 1
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys, xs):
        near = []
        for dy, dx in ((-1, -1), (-1, 0), (-1, 1), (0, -1)):
            ny, nx_ = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx_ < w and labels[ny, nx_]:
                near.append(labels[ny, nx_])
        if not near:
            labels[y, x] = nxt
            parent[nxt] = nxt
            nxt += 1
        else:
            m = min(near)
            labels[y, x] = m
            for n in near:
                union(m, n)
    for k in list(parent):
        parent[k] = find(k)
    return labels, parent


def candidates(path):
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(np.int16)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mask = ((r - np.maximum(g, b)) > RED_MARGIN) & (r > RED_MIN)
    if not mask.any():
        return im.size, []

    labels, parent = label_components(mask)
    gray = np.asarray(im.convert('L')).astype(np.int16)
    h, w = mask.shape

    groups = {}
    ys, xs = np.nonzero(labels)
    for y, x in zip(ys, xs):
        root = parent[labels[y, x]]
        gy = groups.setdefault(root, [w, h, 0, 0, 0])
        gy[0] = min(gy[0], x); gy[1] = min(gy[1], y)
        gy[2] = max(gy[2], x); gy[3] = max(gy[3], y)
        gy[4] += 1

    out = []
    for x0, y0, x1, y1, n in groups.values():
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        diag = (bw ** 2 + bh ** 2) ** 0.5
        fill = n / (bw * bh)
        if diag < MIN_DIAG or fill > MAX_FILL:
            continue                      # 塊は文字・記号、短いものはノイズ
        env = gray[max(0, y0 - MARGIN):y1 + MARGIN, max(0, x0 - MARGIN):x1 + MARGIN]
        if env.size and np.percentile(env, 75) <= PAPER_BRIGHT:
            continue                      # 周りが暗い＝写真・イラストの中
        out.append((y0, x0, bw, bh, int(diag)))
    out.sort()
    return im.size, out


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for path in sys.argv[1:]:
        (w, h), cands = candidates(path)
        print(f'\n=== {os.path.basename(path)} ({w}x{h}) : {len(cands)}件 ===')
        for y0, x0, bw, bh, diag in cands:
            print(f'  縦{y0/h*100:4.0f}% 横{x0/w*100:4.0f}%  '
                  f'{bw}x{bh}px（長さ{diag}）')
        if cands:
            print('  → 各候補を切り出して目視し、手書きか印刷かを判別すること')


if __name__ == '__main__':
    main()
