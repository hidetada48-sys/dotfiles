---
name: x-bookmark-to-notebooklm
description: XのブックマークをテキストファイルとしてGoogle Drive経由でNotebookLMのソースにアップロードする。「Xのブックマークを保存」「ブックマークをNotebookLMに」「x bookmarks sync」などと言ったときに必ず使うこと。Linux・Windows両対応。
---

# X Bookmark → NotebookLM スキル

XのブックマークをPlaywright（ブラウザ自動操作）で取得し、テキストファイルとしてGoogle Driveにアップロードする。NotebookLMはそのGoogle Driveフォルダをソースとして参照できる。

## リポジトリ・ファイル構成

```
~/test2/
└── scripts/
    ├── fetch_bookmarks.py   # メインスクリプト
    └── save_session.py      # 初回のみ：Xセッション保存

~/.x-bookmark-sync/          # 設定・状態ファイル（PC間でGoogle Drive同期）
├── config.json              # 設定ファイル
├── session.json             # Xのセッション（クッキー）
├── processed_ids.json       # 処理済みツイートID
└── output/                  # 生成テキストファイル置き場
```

## 全体フロー

1. Xにセッション認証でログイン → ブックマーク一覧を取得
2. 処理済みIDと照合して新着だけ抽出
3. 各ツイートの詳細ページを開いて全文取得
   - 通常ツイート・X長文記事・引用ツイートに対応
4. 1ブックマーク = 1テキストファイルとして `output/` に保存
5. rcloneでGoogle Drive（`X-Bookmarks-NotebookLM/`）へアップロード
6. 処理済みIDを `processed_ids.json` に記録

---

## 通常実行

```bash
cd ~/test2
python3 scripts/fetch_bookmarks.py
```

件数を指定する場合（「直近N件」と指示されたとき）：

```bash
cd ~/test2
python3 scripts/fetch_bookmarks.py --limit N
```

- 件数指定なし → デフォルト25件（新着のみ）
- `--limit 5` → ブックマーク最新順に最大5件を処理
- ブックマークはXの並び順（ブックマークした新しい順）で取得される

---

## 初回セットアップ（セッション未保存の場合）

```bash
cd ~/test2
python3 scripts/save_session.py
```

ブラウザが起動するのでXにログインする。ログイン完了後、`session.json` が自動保存される。

---

## 設定ファイル（config.json）

```json
{
  "gdrive_remote": "gdrive:",
  "gdrive_folder": "X-Bookmarks-NotebookLM"
}
```

---

## 取得できるコンテンツの種類

| パターン | 対応 |
|---|---|
| 通常ツイート本文 | ✅ |
| X長文記事（記事化投稿）| ✅ |
| 「もっと見る」で展開される長文 | ✅ |
| 引用ツイート（X内の他人の投稿・記事）| ✅ |
| 外部リンク（note、Qiita等） | ❌ |

---

## エラーハンドリング

- **セッション切れ**: `save_session.py` を再実行してXにログインし直す
- **新着0件**: 「新着なし」と報告して終了
- **rclone失敗**: `rclone listremotes` でリモート名を確認する

---

## NotebookLMへの追加方法（初回のみ手動）

1. NotebookLM（notebooklm.google.com）を開く
2. 「ソースを追加」→「Google ドライブ」を選択
3. `X-Bookmarks-NotebookLM` フォルダを選択
4. 以降は新しいファイルが追加されるたびに自動反映される
