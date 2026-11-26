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
  python3 render_html.py <md> <出力名.html>  # 別資料を名前を決めてHTML化（分析レポートを上書きしない）
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
    """レポートmdの本文をHTMLの本文（body内）に変換する
    ★2026-11-26 専務指示「箇条書きごとに枠でくくって見づらい」：枠（カード）をやめ、
      見出し＋番号・箇条の普通のリストにした。字下げした箇条は入れ子のリストにする"""
    out = []      # 出力HTML片
    stack = []    # 開いているリスト（種類 ol/ul と字下げの深さ）

    def close_to(indent):
        # 指定の深さ以上のリストを閉じる
        while stack and stack[-1][1] >= indent:
            out.append(f"</li></{stack.pop()[0]}>")

    for raw in md_text.splitlines():
        line = raw.rstrip()
        m_ol = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
        m_ul = re.match(r"^(\s*)-\s+(.*)$", line)
        if m_ol or m_ul:
            ind = len((m_ol or m_ul).group(1))
            kind = "ol" if m_ol else "ul"
            text = m_ol.group(3) if m_ol else m_ul.group(2)
            close_to(ind + 1)   # これより深いリストは閉じる
            if stack and stack[-1][1] == ind and stack[-1][0] == kind:
                out.append("</li>")   # 同じリストの次の項目
            else:
                if stack and stack[-1][1] == ind:   # 同じ深さで種類が変わる
                    out.append(f"</li></{stack.pop()[0]}>")
                # 番号が1以外から始まる（グループをまたぐ通し番号）ときは start を付ける
                start = f' start="{m_ol.group(2)}"' if m_ol and m_ol.group(2) != "1" else ""
                out.append(f"<{kind}{start}>")
                stack.append((kind, ind))
            out.append(f"<li>{inline(text)}")
            continue
        close_to(0)
        if not line.strip():
            continue
        if line.strip() == "---":
            out.append("<hr>")
        elif line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.startswith("**") and line.endswith("**"):
            out.append(f'<div class="meta">{inline(line)}</div>')
        else:
            out.append(f"<p>{inline(line)}</p>")
    close_to(0)
    return "\n".join(out)


PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  /* ★2026-11-26 枠（カード）をやめた体裁。見出しの下線と番号だけで区切る */
  body{{margin:0;background:#fff;color:#222;line-height:1.8;
    font-family:system-ui,-apple-system,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;}}
  .wrap{{max-width:860px;margin:0 auto;padding:32px 20px 60px;}}
  h1{{font-size:1.5rem;margin:0 0 8px;}}
  h2{{font-size:1.2rem;margin:32px 0 8px;padding-bottom:4px;border-bottom:1px solid #ccc;}}
  h3{{font-size:1.02rem;margin:20px 0 4px;}}
  .meta{{color:#555;font-size:.92rem;}}
  p{{margin:4px 0;}}
  ol,ul{{margin:4px 0;padding-left:1.6em;}}
  li{{margin:3px 0;}}
  hr{{border:none;border-top:1px solid #ddd;margin:28px 0;}}
  /* ★2026-11-26 専務指示：P1〜P3 は色の四角に白い太字（本文と同じ大きさ）で目立たせる */
  .tag{{display:inline-block;color:#fff;font-weight:700;font-size:1em;line-height:1.4;
    padding:0 7px;border-radius:4px;margin-right:6px;}}
  .p1{{background:#d0392b;}} .p2{{background:#d9822b;}} .p3{{background:#2e6db4;}}
  a{{color:#2e6db4;}}
  code{{background:#f1f1f1;padding:0 4px;border-radius:3px;font-size:.92em;}}
  footer{{margin-top:40px;color:#888;font-size:.82rem;text-align:center;}}
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
    # 分析レポート以外（項目の説明などの別資料）は、md の1行目の見出しを題名にする
    h1 = re.search(r"^# (.+)$", md_text, re.M)
    if not md_path.name.endswith("分析.md") and h1:
        title = h1.group(1)
    body = md_to_body(md_text)
    # 3つ目の引数で出力の名前を決められる（別資料が分析レポートの HTML を上書きしないように）
    out_name = sys.argv[2] if len(sys.argv) > 2 else out_html_name(md_path)
    out_path = BOOKMARKS_DIR / out_name
    out_path.write_text(PAGE.format(title=html.escape(title), body=body), encoding="utf-8")

    ensure_server()
    url = f"http://{HOST}:{PORT}/{out_name}"
    print(f"OK: {out_path}")
    print(f"URL: {url}")


if __name__ == "__main__":
    main()
