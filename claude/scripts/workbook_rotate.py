#!/usr/bin/env python3
"""ワークブック画像をEXIFタグに従って回転し、orientationタグを除去して保存する"""
import sys
import os
from PIL import Image

# EXIF orientation値 → PIL rotate引数（負=CW、正=CCW）
ROTATION_MAP = {1: 0, 3: 180, 6: -90, 8: 90}

def rotate_by_exif(path):
    img = Image.open(path)
    orientation = img.getexif().get(274, 1)
    degrees = ROTATION_MAP.get(orientation, 0)
    before = img.size

    if degrees != 0:
        img = img.rotate(degrees, expand=True)

    # orientationタグを除去（EXIFを意識するビューアによる二重補正を防ぐ）
    exif = img.getexif()
    if 274 in exif:
        del exif[274]

    img.save(path, format='JPEG', quality=95, exif=exif.tobytes())
    return orientation, degrees, before, img.size

def process_folder(folder_path):
    extensions = ('.jpg', '.jpeg', '.JPG', '.JPEG')
    files = sorted([f for f in os.listdir(folder_path) if f.endswith(extensions)])

    if not files:
        print(f"対象ファイルなし: {folder_path}")
        return

    print(f"対象: {len(files)}枚")
    for fname in files:
        fpath = os.path.join(folder_path, fname)
        orientation, degrees, before, after = rotate_by_exif(fpath)
        direction = {-90: "CW", 90: "CCW", 180: "180°", 0: "なし"}.get(degrees, str(degrees))
        print(f"  {fname}: EXIF={orientation} → {direction} ({before[0]}x{before[1]} → {after[0]}x{after[1]})")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使い方: python3 workbook_rotate.py <フォルダパス>")
        sys.exit(1)
    process_folder(sys.argv[1])
