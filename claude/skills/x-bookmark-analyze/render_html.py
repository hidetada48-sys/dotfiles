#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ブックマーク分析レポート（md）を、見やすいHTMLに変換してクリックで開けるようにする道具。

- 外部ライブラリ不要（標準ライブラリだけ）＝ Windows PC でもそのまま動く
- 原本の md はそのまま温存する（触らない）
- 生成した HTML は同じ ~/test2/bookmarks/ に英数字ファイル名で置く（クリックで開きやすい）
- 127.0.0.1 限定の簡易サーバーで配信し、クリックできるURLを標準出力に返す

使い方:
  python3 render_html.py                 # bookmarks内の最新「*分析.md」を自動でHTML化して配信
  python3 render_html.py <分析md>        # 指定した分析mdをHTML化して配信
  ※ Windowsは python、Linux/WSLは python3 で呼ぶ（中身は共通）
"""

import sys
import os
import re
import glob
import html
import subprocess
from datetime import date
from pathlib import Path
from urllib.request import urlopen

BOOKMARKS_DIR = Path(os.path.expanduser("~/test2/bookmarks"))  # レポート置き場
HOST = "127.0.0.1"   # 自PC内のみ（社外非公開）
PORT = 8777          # 配信ポート（固定）


def find_latest_md() -> Path:
    """最新の「*分析.md」を1つ選ぶ（インデックス等は除外）"""
    files = [Path(p) for p in glob.glob(str(BOOKMARKS_DIR / "*分析.md"))]
    if not files:
        print("NOT_FOUND: 分析mdが見つかりません")
        sys.exit(1)
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def out_html_name(md_path: Path) -> str:
    """英数字のHTMLファイル名を作る（ファイル名の日付を使い、無ければ今日）"""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", md_path.name)  # 例: 2026-07-25
    stamp = m.group(1) if m else date.today().isoformat()
    return f"bookmark_analysis_{stamp}.html"


# ---- ここから md → html の簡易変換（このレポートの書式に特化）----

def inline(text: str) -> str:
    """行内の記法（太字・リンク・コード・優先度タグ）をHTMLに変換する"""
    text = html.escape(text)
    # markdownリンク [題名](URL) → <a>
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)",
                  r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    # コード `xxx` → <code>
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # 太字 **xxx** → <strong>
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # 優先度タグ [P1]/[P2]/[P3] → 色付きバッジ
    text = re.sub(r"\[P1\]", '<span class="tag p1">P1</span>', text)
    text = re.sub(r"\[P2\]", '<span class="tag p2">P2</span>', text)
    text = re.sub(r"\[P3\]", '<span class="tag p3">P3</span>', text)
    return text


def md_to_body(md_text: str) -> str:
    """レポートmdの本文をHTMLの本文（body内）に変換する"""
    lines = md_text.splitlines()
    out = []          # 出力HTML片
    ul_open = False   # <ul>を開いている最中か

    def close_ul():
        nonlocal ul_open
        if ul_open:
            out.append("</ul>")
            ul_open = False

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            close_ul()
            continue
        # 区切り線
        if line.strip() == "---":
            close_ul()
            continue
        # 見出し
        if line.startswith("### "):
            close_ul()
            out.append(f"<h3>{inline(line[4:])}</h3>")
            continue
        if line.startswith("## "):
            close_ul()
            out.append(f"<h2>{inline(line[3:])}</h2>")
            continue
        if line.startswith("# "):
            close_ul()
            out.append(f'<h1>{inline(line[2:])}</h1>')
            continue
        # 番号付き項目（1. ... ）→ カード
        m = re.match(r"^\d+\.\s+(.*)$", line)
        if m:
            if not ul_open:
                out.append('<ul class="items">')
                ul_open = True
            num = line.split(".", 1)[0]
            out.append(f'<li class="item"><span class="num">{num}.</span>{inline(m.group(1))}</li>')
            continue
        # 箇条書き（- ... ）→ カード
        if line.startswith("- "):
            if not ul_open:
                out.append('<ul class="items">')
                ul_open = True
            out.append(f'<li class="item">{inline(line[2:])}</li>')
            continue
        # 「**作成日：...**」など meta 行
        if line.startswith("**") and line.endswith("**"):
            close_ul()
            out.append(f'<div class="meta">{inline(line)}</div>')
            continue
        # それ以外は段落（リード文など）
        close_ul()
        out.append(f'<p class="lead">{inline(line)}</p>')

    close_ul()
    return "\n".join(out)


PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  :root{{--p1:#e6462e;--p2:#e08a1e;--p3:#3a7bd5;--bg:#f7f7f5;--card:#fff;--ink:#2b2b2b;--muted:#777;--line:#e5e2dc;}}
  *{{box-sizing:border-box;}}
  body{{margin:0;background:var(--bg);color:var(--ink);line-height:1.75;
    font-family:system-ui,-apple-system,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;}}
  .wrap{{max-width:860px;margin:0 auto;padding:32px 20px 80px;}}
  h1{{font-size:1.6rem;margin:0 0 6px;border-bottom:3px solid var(--ink);padding-bottom:14px;}}
  h2{{font-size:1.2rem;margin:34px 0 12px;padding-left:12px;border-left:5px solid var(--ink);}}
  h3{{font-size:1rem;margin:20px 0 8px;color:#444;}}
  .meta{{color:var(--muted);font-size:.9rem;}}
  .lead{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:14px 0;}}
  ul.items{{padding-left:0;list-style:none;margin:0;}}
  li.item{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:10px 0;}}
  .num{{font-weight:700;color:var(--muted);margin-right:6px;}}
  .tag{{display:inline-block;color:#fff;font-size:.72rem;font-weight:700;padding:2px 8px;border-radius:999px;margin-right:8px;}}
  .p1{{background:var(--p1);}} .p2{{background:var(--p2);}} .p3{{background:var(--p3);}}
  a{{color:var(--p3);}}
  code{{background:#eee;padding:1px 5px;border-radius:4px;font-size:.9em;}}
  footer{{margin-top:40px;color:var(--muted);font-size:.82rem;text-align:center;}}
</style>
</head>
<body>
<div class="wrap">
{body}
<footer>Xブックマーク週次分析 ／ x-bookmark-analyze</footer>
</div>
</body>
</html>
"""


def ensure_server():
    """配信サーバーが動いていなければ起動する（起動済みなら何もしない）"""
    url = f"http://{HOST}:{PORT}/"
    try:
        urlopen(url, timeout=1)
        return  # 既に稼働中
    except Exception:
        pass
    # バックグラウンドで起動（このスクリプトが終わっても生き続ける）
    subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", HOST],
        cwd=str(BOOKMARKS_DIR),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def main():
    md_path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else find_latest_md()
    if not md_path.exists():
        print(f"NOT_FOUND: {md_path}")
        sys.exit(1)

    md_text = md_path.read_text(encoding="utf-8")
    m = re.search(r"\d{4}-\d{2}-\d{2}", md_path.name)  # ファイル名から日付を拾う
    title = f"ブックマーク分析レポート {m.group(0)}" if m else "ブックマーク分析レポート"
    body = md_to_body(md_text)
    out_name = out_html_name(md_path)
    out_path = BOOKMARKS_DIR / out_name
    out_path.write_text(PAGE.format(title=html.escape(title), body=body), encoding="utf-8")

    ensure_server()
    url = f"http://{HOST}:{PORT}/{out_name}"
    print(f"OK: {out_path}")
    print(f"URL: {url}")


if __name__ == "__main__":
    main()
