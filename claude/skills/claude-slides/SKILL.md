---
name: claude-slides
description: claude.ai のスライド（Slides の型）でスライドを作り、絵が要るページは Gemini（Nano Banana Pro）で描いて入れる。「/claude-slides ○○」「claude.ai のスライドで○○」「休日モード　○○のスライドを作って」と言われたときに使う。
when_to_use: 専務モードの「スライドにして」「説明資料にして」（社内の説明資料＝md で作り目次に載る形）は setsumei-shiryo を使い、このスキルは使わない。迷ったら「claude.ai のスライドか、社内の説明資料か」を1行で伺う。
argument-hint: "[スライドの題]"
---

# claude.ai のスライド ＋ Gemini の画像生成（2026-11-27 専務「作れ」）

claude.ai の Slides の型でスライドを作り、絵は Gemini で描いて入れる。この2つを1組で使う。
設計書＝mino-sakura-hq `docs/plans/2026-11-27-claude.aiのスライドと画像生成をスキルに.md`
見本＝前立腺がんのスライド（https://claude.ai/artifact/W7wCMC8tb2KUXSFwjVeKNU・控え＝mino-sakura-hq `holiday/reports/2026-11-26_前立腺がんのスライド.md`）

## 手順

1. **スライドの型を呼ぶ**
   - Artifact ツールで publish：`type_url` ＝ `https://claude.ai/artifact/8jTsAFQMFDb2oA8MsPJ2eL`（Slides の型）、`title` ＝ スライドの題、`auto_open: "after_first_write"`、ファイルは付けない
   - 型のリンクで作れなければ、`action: "list"`・`scope: "types"` で「Slides」を探し、そのリンクを使う
   - 返ってきた `url` と型の手順（型の SKILL.md）に従って作る。作るファイルは `project/deck.json`・`project/deck.css`・`project/slides/<id>.html`
   - 作業の置き場（`root`）はスクラッチパッドの中の1つのフォルダ
2. **中身を決める**
   - 題からページの並びを決める。数字・事実は信頼できる出典（官公庁・学会など）で確かめ、最後のページに出典を並べる
   - スライドの色は題材の内容に合わせて選ぶ。専務や弊社に寄せない（2026-11-27 専務「それでいい」）
3. **絵を描く（Gemini）**
   - 絵が要るページ（表紙・人物・場面など）を決め、1枚ずつ描く。描くのは既にある画像生成のプログラム（`~/dotfiles/claude/scripts/generate_image.py`・/generate-image と同じ）
   - 鍵は日報アプリの Gemini の鍵を、その場で読んで渡す（2026-11-26 専務承認）。鍵を画面や記録に出さない：
     ```bash
     GOOGLE_API_KEY="$(sed -n 's/^KEY=//p' '//LS510DcB3/mino_data/18_共用アプリ/抄紙日報/日報アプリ/鍵.txt')" \
     PYTHONIOENCODING=utf-8 python ~/dotfiles/claude/scripts/generate_image.py "英語の指示文" --output <スクラッチパッド>/<名前>.png
     ```
   - Linux は社内サーバーに届かない＝パソコンの設定に `GOOGLE_API_KEY` があればそれを使い、無ければ絵を描けないことを専務に伝える
   - 人物・背景・景色・小物・雰囲気は題材の内容に合わせて選ぶ。年齢や姿を専務に似せない。山・川・緑茶など弊社の土地の風景を勝手に入れない（2026-11-27 Claude Duet の表紙の件）
   - 1枚約20円。10枚以上描くときは、先に枚数と費用を伺う
   - 描いた絵は Read で見て、そのページの中身に合うかを確かめる
4. **絵をスライドに入れる**
   - Artifact ツールで `{action:"publish", url:<スライドの url>, file_path:<絵のファイル>, asset:true}` → 返った `url`（`/_blob/<id>`）をそのまま `<img src>` に書く
   - `<img>` には `width`・`height` を付ける。写真や場面の絵は `object-fit:cover`
5. **確かめて出す**
   - 専務の Chrome でスライドを開き、ページごとに文字のはみ出しと絵の表示を確かめる
   - 専務への返答は、スライドのリンクと、絵の枚数・費用（例：絵7枚・約140円）
6. **控えを残す（休日モードのとき）**
   - `holiday/reports/{日付}_{題}.md` に、スライドのリンク・ページごとの中身・絵の描き方と費用・出典を書く（前立腺がんの控えと同じ形）
