---
name: notebooklm-research
description: notebooklm-py CLIを使ってNotebookLMで調査する。「notebooklmで調査して」「notebooklmで調べて」と言ったときに使う。Jina/WebSearchで代替しない。
---

# NotebookLM調査スキル

## 概要
`notebooklm-py` CLIを使ってNotebookLMに新しいノートブックを作成し、3パターンのクエリで情報収集する。ユーザーはクエリ（調査テーマ）を渡すだけでよい。ノートブック名・手順の確認は不要。

## 手順

1. **ノートブックを作成する**
   ```bash
   notebooklm create "調査テーマ名"
   ```
   返ってきたノートブックIDを次のステップで使う。

2. **3パターンで情報源を追加する**
   ```bash
   notebooklm source add-research -n [ID] "クエリ note記事" --import-all
   notebooklm source add-research -n [ID] "クエリ X投稿" --import-all
   notebooklm source add-research -n [ID] "クエリ" --import-all
   ```

3. **追加クエリを提案する**
   調査テーマに応じて有効そうな追加クエリがあればユーザーに提案し、必要なら追加する。

## 注意事項
- Jina/WebSearchで代替しない
- `notebooklm-py` が未インストールの場合は `notebooklm login` を案内する
