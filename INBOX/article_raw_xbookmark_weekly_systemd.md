# 記事素材（生・時系列）：systemdでXブックマーク週次収集を完全自動化した話

**収集方針：割愛・要約せず、会話・やり取り・詰まりポイントも含めて時系列に並べる**
**対象期間：2026-04-07 〜 2026-04-14**

---

## ■ Phase 0：v1（fetch_bookmarks.py）の運用と問題（〜2026-04-07）

### 2026-04-07：ブックマーク収集作業

**実施内容：**
- 3/27以降の未収集ブックマークを収集
- 取得件数：**27件**（3/27〜4/5）
- Google Driveへのアップロード完了
- 累計取得数：87件（3/17〜4/5）

**発生した問題：`No module named 'playwright'` エラー**

```
cd ~/test2 && python3 scripts/fetch_bookmarks.py
→ No module named 'playwright'
```

- 原因：`~/.bashrc` に `~/.browser-use-env/bin` がPATHの先頭に追加されており、`python3` コマンドがbrowser-use用の仮想環境を参照していた
- browser-useは2026-03-28にインストールされ、インストール当日しか使われていなかった

**対処1：~/.bashrcのPATH修正**
- `~/.bashrc` から以下の行を削除
  ```
  # Browser-Use
  export PATH="/home/hidetada48/.browser-use-env/bin:/home/hidetada48/.local/bin:$PATH"
  ```
- browser-use自体は削除せず残した

**対処2：スクリプトのシバン行を修正**
- `fetch_bookmarks.py` の1行目を変更
  - 変更前：`#!/usr/bin/env python3`
  - 変更後：`#!/usr/bin/python3`
- PATH環境に依存せず正しいPythonが使われるようになった

**この時点でのv1の状態：**
- 手動実行で動く
- 出力：個別.txtファイル → `~/.x-bookmark-sync/output/`
- GDriveフォルダ：`X-Bookmarks-NotebookLM/`
- スケジュール実行なし（毎回手動）

---

## ■ Phase 1：v2設計・実装（2026-04-09）

### v1からv2への方針転換

**v1の課題：**
- 毎回手動で実行する必要がある
- 出力が個別.txtで分散している
- NotebookLMへのアップロードが目的だったが、Claudeに直接読ませる方が早いと気づいた

**v2の設計：**
- 週次で自動実行（systemdタイマー）
- 出力を週次統合.md（`bookmarks_MMDD-MMDD.md`）にまとめる
- Claude Codeスキルとして定義し、AIがインデックスファイルも自動生成
- GDriveに自動アップロード

### 作成ファイル

- `~/test2/scripts/fetch_bookmarks_v2.py` — 収集スクリプト（Playwright）
- `~/test2/SKILL_V2.md` — Claude Codeスキル定義
- `~/test2/bookmarks/` — 出力フォルダ
- `~/.config/systemd/user/x-bookmark-weekly.service` — systemdサービス
- `~/.config/systemd/user/x-bookmark-weekly.timer` — systemdタイマー

### v1とv2の違い

| 項目 | v1 | v2 |
|---|---|---|
| 出力形式 | 個別.txtファイル | 週次統合.mdファイル |
| 保存先 | `~/.x-bookmark-sync/output/` | `~/test2/bookmarks/` |
| インデックス | なし | `bookmarks_index_MMDD-MMDD.md` を自動生成（AI） |
| GDriveフォルダ | `X-Bookmarks-NotebookLM/` | `X-Bookmarks-Weekly/` |
| 収集開始日 | 制限なし | 2026-04-06以降のみ |
| 実行 | 手動 | systemdタイマー（毎週火曜 00:00 JST） |

### v2の運用フロー

```
1. systemdタイマーが毎週火曜 00:00 JSTにclaude CLIを起動
2. x-bookmark-weeklyスキルが発動
3. fetch_bookmarks_v2.py でXブックマーク収集 → 週次統合md作成
4. ClaudeがインデックスファイルをAI生成（カテゴリ分類・概要付き）
5. rcloneでGDrive（X-Bookmarks-Weekly/）に統合ファイルをアップロード
```

### fetch_bookmarks_v2.py の引数

```bash
python3 scripts/fetch_bookmarks_v2.py              # 通常（新着のみ）
python3 scripts/fetch_bookmarks_v2.py --from 2026-04-06 --to 2026-04-06  # 期間指定
python3 scripts/fetch_bookmarks_v2.py --limit 10   # 件数制限
```

### 処理済みID管理

- `~/.x-bookmark-sync/processed_ids_v2.json`（v1と独立）
- 収集開始：2026-04-06以降

### このセッションで発覚した問題・対処

- brainstormingスキルを発動せずに実装開始 → CLAUDE.mdに「新機能前にbrainstorming必須」を追加
- health スキルが的外れな報告 → descriptionを「明示的依頼時のみ使用」に制限
- fetch_bookmarks_v2.pyに--from/--toが抜けていた → v1から移植して修正

### コミット

- test2: `62e36e7` 週次ブックマーク収集v2を追加

---

## ■ Phase 2：「動いていない」発覚（2026-04-14）

### 状況

v2実装から約5日後（2026-04-14）。systemdタイマーを確認しても、一度も自動実行されていない。

**ユーザーの第一声：**
> 「systemdサービスが動いていなかった」

### 調査：原因① systemdが環境変数を引き継がない

systemdはログインシェルのセッションとは独立して動く。つまり：

- `.bashrc`で設定したPATH → systemdには渡らない
- `HOME`変数 → 未設定
- `~/.cargo/bin`（rtk）→ 参照できない
- Claude CLIの認証トークン → `HOME`がないと見つけられない

結果：`claude` コマンドを起動しようとしても **401エラー**（認証失敗）で即終了していた。

**serviceファイルの変更前（問題あり）：**
```ini
[Service]
ExecStart=/bin/bash -c 'cd ~/test2 && claude --print ...'
```

**serviceファイルの変更後（修正後）：**
```ini
[Service]
Environment=HOME=/home/hidetada48
Environment=PATH=/home/hidetada48/.local/bin:/home/hidetada48/.cargo/bin:/usr/local/bin:/usr/bin:/bin
TimeoutStartSec=5400
ExecStart=/bin/bash -c 'cd ~/test2 && claude --print ...'
```

- `HOME` を明示的に設定 → 認証トークンを正しく参照できる
- `PATH` を明示的に設定 → `claude`、`rclone`、`python3` が見つかる
- `TimeoutStartSec=5400` → 90分のタイムアウト設定（長時間処理に対応）

### 調査：原因② スキルが `~/.claude/skills/` に未登録

`SKILL_V2.md` は `~/test2/` リポジトリに置いてあるだけで、Claude Codeがスキルとして認識する `~/.claude/skills/` に登録されていなかった。

**問題：**
```
~/test2/SKILL_V2.md  ← ここにあるだけ
~/.claude/skills/    ← x-bookmark-weeklyが存在しない
```

スキルが登録されていないため、`x-bookmark-weekly` を呼び出しても何も発動しない。

**修正：** dotfilesのスキル管理方式でシンボリックリンクを作成

```bash
mkdir ~/dotfiles/claude/skills/x-bookmark-weekly
ln -s ~/test2/SKILL_V2.md ~/dotfiles/claude/skills/x-bookmark-weekly/SKILL.md
ln -s ~/dotfiles/claude/skills/x-bookmark-weekly ~/.claude/skills/x-bookmark-weekly
```

dotfilesにコミット（commit: 9bb0082「x-bookmark-weeklyスキルを登録」）。

---

## ■ Phase 3：動作確認（2026-04-14）

### テスト実行

原因が2つわかったので修正後、タイマーを `20:15 JST` に変更してテスト実行。

**結果：成功**

```
収集件数：2件（4/13分）
インデックス作成：完了
GDriveアップロード：完了
所要時間：約12分
```

12分かかった理由：
- ClaudeがPlaywrightでXにアクセス
- ブックマーク一覧をスクロールして取得
- 統合mdファイル作成
- AIによるインデックス生成（カテゴリ分類・概要付き）
- rcloneでGDriveアップロード

### タイマー設定を本番に戻す

```
OnCalendar=Mon *-*-* 15:00:00 UTC  # 毎週火曜 00:00 JST
Persistent=true
```

次回自動実行：2026-04-21（火）00:00 JST

### データ状況（修正後）

`~/test2/bookmarks/` に以下が存在：
- `bookmarks_0405-0405.md` — GDriveから復元
- `bookmarks_0407-0413.md` — GDriveから復元（23件）
- `bookmarks_index_0407-0413.md` — エージェントで再生成（7カテゴリ）
- `bookmarks_0413-0413.md` — テスト分（2件）
- `bookmarks_index_0413-0413.md` — テスト分

`processed_ids_v2.json`：2件（4/13分のみ記録）
※ 4/7-4/12分はprocessed_ids_v2.jsonに未記録（GDriveからmdは復元済み）

---

## ■ Phase 4：Discord通知追加（2026-04-14 深夜）

### 動機

「自動実行が完了してもどこにも通知が来ない。気づかない」

### 実装

1. `~/test2/.discord_webhook` にWebhook URLを保存（秘密情報）
2. `SKILL_V2.md` にステップ4（Discord通知）を追加
3. `.gitignore` に `.discord_webhook` を追加（Webhookトークンをgit管理外に）

**Discord通知の仕様：**
```
週次ブックマーク収集完了
件数: N件
ファイル: bookmarks_MMDD-MMDD.md
```
- `.discord_webhook` ファイルが存在すれば送信
- 存在しない場合はスキップ（Webhookなし環境でも動く）

**スクリーンショット削除：**
Discord設定手順で作成されたと思われるスクリーンショット20枚を削除。コミットせず不要ファイルとして削除。

### コミット

- test2: `ddb4550` v2スキルにDiscord通知ステップを追加・.discord_webhookをgitignoreに追加
- dotfiles: `5867b58` x-bookmark-weeklyスキルを登録：weekly収集の自動実行に対応（push済み）

---

## ■ 全体のコミット時系列

### test2リポジトリ

| コミット | 内容 |
|----------|------|
| `62e36e7` | 週次ブックマーク収集v2を追加：統合mdファイル+インデックス生成に対応 |
| `fd3fe98` | bookmarksディレクトリを追加：v2週次収集の出力を管理 |
| `ddb4550` | v2スキルにDiscord通知ステップを追加・.discord_webhookをgitignoreに追加 |

### dotfilesリポジトリ

| コミット | 内容 |
|----------|------|
| `5867b58` | x-bookmark-weeklyスキルを登録：weekly収集の自動実行に対応 |

---

## ■ 詰まりポイント まとめ

| # | 問題 | 原因 | 対処 |
|---|------|------|------|
| 1 | python3がplaywright未インストールエラー（v1） | browser-use仮想環境がPATHの先頭にいた | ~/.bashrcのPATH修正 + シバン行を絶対パスに |
| 2 | systemdタイマーが5日間一度も動かなかった | systemdはログインシェルの環境変数を引き継がない | serviceファイルにHOME/PATH/TimeoutStartSecを明示 |
| 3 | スキルが発動しなかった | SKILL_V2.mdをtest2に置いただけで~/.claude/skills/未登録 | dotfiles経由のシンボリックリンクで正式登録 |

---

## ■ 現在の状態（2026-04-14 完了時点）

- **systemdサービス：** 動作確認済み（12分でフロー完走）
- **スキル登録：** ~/.claude/skills/x-bookmark-weekly → 有効
- **Discord通知：** 設定済み
- **次回自動実行：** 2026-04-21（火）00:00 JST

---

## ■ 補足：関連して起きた別の問題（参考）

この作業と並行して、dotfiles管理周りの問題が複数発生した（別記事候補）：

- **basic-memory競合問題**（2026-04-13）：rclone sync がLinux/Windows間でノートを削除し合う → rclone copy に変更
- **RTK GLIBC不一致問題**（2026-04-14）：新しいrtk バイナリがGLIBC 2.39を要求するがLinuxは2.36 → ソースからビルドで解決
- **RTK Windows対応**（2026-04-14）：WindowsデスクトップはフックベースのRTK非対応のため、OS判定スキップを追加
