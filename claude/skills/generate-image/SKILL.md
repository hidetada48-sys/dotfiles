---
name: generate-image
description: Gemini（Nano Banana Pro）でAI画像を生成する。「画像生成して」「generate image」「画像を作って」と言ったときに使う。
---

# 画像生成スキル（Nano Banana Pro）

## 概要
`~/dotfiles/claude/scripts/generate_image.py` を使って Gemini（Nano Banana Pro）で画像を生成する。

## 手順

1. **プロンプトを確認する**
   - ユーザーが日本語で説明した場合は英語プロンプトに変換する
   - プロンプトが曖昧なら「どんな画像にしますか？」と確認する

2. **スクリプトを実行する**
   ```bash
   python3 ~/dotfiles/claude/scripts/generate_image.py "英語プロンプト" --output 保存先.png
   ```
   - `--output` を省略すると現在のディレクトリに `generated_YYYYMMDD_HHMMSS.png` で保存される
   - モデルを変えたい場合は `--model gemini-3.1-flash-image-preview` のように指定

3. **生成結果を表示する**
   - 保存されたファイルを Read ツールで読んでユーザーに見せる

## 注意事項
- `GOOGLE_API_KEY` が環境変数に設定されていること（未設定ならエラーが出る）
- 1回の実行で1枚生成（複数枚必要なら複数回実行）
- 10枚以上生成する場合は事前にユーザーに確認する（コスト管理）

## モデル一覧
| ニックネーム | モデルID | 特徴 |
|---|---|---|
| Nano Banana Pro（デフォルト） | `gemini-3-pro-image-preview` | 高画質・写実的 |
| Nano Banana 2 | `gemini-3.1-flash-image-preview` | 高速・大量生成向け |
| Nano Banana | `gemini-2.5-flash-image` | 低遅延・軽量 |
