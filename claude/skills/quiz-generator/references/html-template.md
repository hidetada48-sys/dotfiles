# 問題集HTML テンプレート（3skill共通）

quiz-generator / mock-test-generator が出力するHTMLの唯一の手本。
**このファイルが体裁の正典。** 3つのskillは必ずここを読んでから生成する。

参照パス（両OS共通・チルダ形式で書くこと）：
`~/.claude/skills/quiz-generator/references/html-template.md`

---

## 1. 大原則

- **出力はHTML1本**。docx・PDFは作らない。印刷が要るときはブラウザの「印刷 → PDFに保存」を使う
- **レイアウト目的の表組みを使わない**。氏名欄・解答欄は罫線付きの `div` で組む
  （旧docx版では解答欄に表を13個使っていた。Googleドキュメント変換で崩れる原因だった）
- **図・地図・写真は埋め込まない**（著作権）。原本参照は赤字の注記で示す
- **1ファイル完結**。CSSは `<style>` に内包し、外部ファイル・CDNを参照しない

---

## 2. 骨組み

```html
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>【教科】【単元】 類似・関連問題集</title>
<style>/* 3節のCSSをそのまま貼る */</style>
</head>
<body>
<div class="page">
  <h1>正負の数　類似・関連問題集</h1>
  <p class="sub">数学 1年 第1章</p>

  <div class="namebar"><span>氏　名</span><i></i><span>日　付</span><i></i></div>
  <p class="note">※ 類似問題（水色）→ 関連問題（オレンジ）の順に取り組もう</p>

  <!-- 出典ごとに section を繰り返す -->
  <section>
    <h2>◆ p.5 ⑥(1)　数の大小・並べ替え</h2>

    <p class="tag sim">【類似問題】</p>
    <p>次の数を小さい順に並べなさい。</p>
    <p class="expr">-2.5,　+4,　-1/3,　0,　+3/4,　-3/2</p>
    <div class="ans"><span class="lbl">答え：</span><i></i></div>

    <p class="tag rel">【関連（応用）問題】</p>
    <p>次の数について、絶対値が最も大きい数と最も小さい数を答えなさい。</p>
    <p class="expr">-1/4,　+3,　-2.8,　0,　+1/2,　-5/3</p>
    <div class="ans"><span class="lbl">答え：</span><i></i><i></i></div>
  </section>

  <!-- 巻末①解答一覧・巻末②解説は改ページしてから -->
  <div class="pagebreak"></div>
  <h2 class="back">巻末①　解答一覧</h2>
  <p class="ansrow"><b>p.5 ⑥(1) 問1（類似）：</b> -5/2, -3/2, -1/3, 0, 3/4, 4</p>

  <div class="pagebreak"></div>
  <h2 class="back">巻末②　解説</h2>
  <div class="exp">
    <p class="expttl">p.5 ⑥(1) 問1（類似）</p>
    <p>解説の本文。考え方と間違えやすい点を書く。</p>
  </div>
</div>
</body>
</html>
```

---

## 3. CSS（そのまま使う。色は変えない）

```css
:root{
  --ink:#1a1a1a; --rule:#c8c8c8;
  --head:#1f4e79;   /* 見出し・出典ラベルの紺 */
  --sim:#1f6aab;    /* 類似問題の青 */
  --rel:#c55a11;    /* 関連問題のオレンジ */
  --band:#d5e8f0;   /* 氏名欄の水色 */
  --thin:#666;
}
*{box-sizing:border-box}
body{margin:0;background:#f2f3f5;color:var(--ink);
  font-family:"Yu Gothic","Hiragino Kaku Gothic ProN","MS Gothic",sans-serif}
.page{width:210mm;min-height:297mm;margin:14px auto;padding:18mm 16mm;background:#fff;
  box-shadow:0 2px 14px rgba(0,0,0,.14)}

h1{margin:0 0 4px;font-size:20pt;font-weight:700;color:var(--head)}
.sub{margin:0 0 14px;font-size:12pt;color:var(--thin)}
.note{margin:8px 0 18px;font-size:10pt;color:#888}

.namebar{display:flex;align-items:baseline;gap:10px;background:var(--band);
  padding:9px 12px;margin:10px 0 4px;font-size:11pt}
.namebar i{flex:1;border-bottom:1px solid #7ea8bd;height:1.15em}

section{margin:0 0 22px}
h2{margin:22px 0 10px;font-size:12pt;font-weight:700;color:var(--head);
  border-bottom:1.5px solid var(--head);padding-bottom:3px}
h2.back{border-bottom-width:2px}

p{margin:0 0 6px;font-size:11pt;line-height:1.75}
.tag{font-weight:700;font-size:11pt;margin-top:10px}
.tag.sim{color:var(--sim)}
.tag.rel{color:var(--rel)}
.expr{margin-left:1em;font-family:"MS Gothic",monospace;letter-spacing:.02em}
.src{color:#c00000;font-weight:700}   /* ※ワークP.◯の図を見て答えなさい */

.ans{margin:2px 0 14px}
.ans .lbl{font-size:11pt;color:#999}
.ans i{display:block;border-bottom:1px solid var(--rule);height:1.9em;margin-top:2px}

.ansrow{margin:0 0 5px;font-size:10.5pt}
.exp{margin:0 0 14px}
.expttl{font-weight:700;color:var(--sim);margin-bottom:2px}

.pagebreak{break-before:page}

@media print{
  body{background:#fff}
  .page{width:auto;min-height:0;margin:0;padding:0;box-shadow:none}
  section{break-inside:avoid}
  @page{size:A4;margin:16mm}
}
@media (max-width:820px){          /* スマホで見るとき */
  .page{width:auto;margin:0;padding:14px;box-shadow:none}
}
```

---

## 4. 部品の使い分け

| 用途 | 使うもの | 使ってはいけないもの |
| --- | --- | --- |
| 氏名・日付欄 | `.namebar`（flex＋下罫線） | `<table>` |
| 解答欄1行 | `.ans` に `<i>` 1つ | `<table>` |
| 解答欄を複数行 | `<i>` を必要な数だけ並べる | `<br>` の連打 |
| 出典の見出し | `h2`（下に紺の罫線） | 背景色ベタ塗り |
| 類似／関連のラベル | `.tag.sim` / `.tag.rel` | 独自の色 |
| 原本参照の注記 | `.src`（赤字） | 図の埋め込み |
| 数式・数の並び | `.expr` | 全角スペースでの位置合わせ |

---

## 5. 生成のしかた

Pythonで文字列として組み立て、UTF-8で書き出す。外部ライブラリは要らない。

```python
from html import escape
# 問題文はユーザーの写真から起こしたテキスト。必ず escape してから埋める
body.append(f'<p>{escape(q["text"])}</p>')
open(path, 'w', encoding='utf-8').write(doc)
```

書き出したら**必ずブラウザで開いて体裁を目視確認してから**提示する。
（旧docx版では `pdftoppm` で画像化して確認していた。HTMLは直接見えるのでその手順は不要）

---

## 6. ファイル名と置き場

- ファイル名：`<教科>_<単元>_類似関連問題集.html`（模擬は `_模擬テスト`）
- ログJSON：`<同じベース名>_log.json`
- 置き場：作業は一時フォルダ。完成したらDriveの教材フォルダへ `rclone copy` する
