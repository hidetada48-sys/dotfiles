# Claude Code × Discord 連携セットアップ作業ログ

**作業日**: 2026年4月1日〜2日  
**目的**: Claude Code の Discord プラグインを使って、Discord の DM からClaudeに話しかけられるようにする

---

## 背景・前提

- 環境: Chromebook Crostini（Linux コンテナ）
- Claude Code バージョン: Sonnet 4.6
- Discord プラグイン: `discord@claude-plugins-official`（公式プラグイン）
- 使用ツール: Playwright MCP（ブラウザ自動操作）

---

## 作業履歴（時系列）

### 1. 接続状況の確認

**ユーザーの質問**: 「discordにつながってますか？」

`~/.claude/settings.json` を確認したところ、`enabledPlugins` に以下が存在：

```json
"discord@claude-plugins-official": true
```

プラグイン自体は有効。ただし `~/.claude/channels/discord/access.json` が存在せず、セットアップ未完了と判明。

---

### 2. 現状調査

**調査結果**:

| 項目 | 状態 |
|------|------|
| プラグイン設定 | 有効 |
| `.env`（トークンファイル） | 存在（91バイト）|
| サーバープロセス | 起動中（`claude --channels plugin:discord@claude-plugins-official`）|
| `access.json` | **未作成** |
| ボットのDiscord表示 | **オフライン** |

- プロセスツリーに `bun` プロセス（Discord ボットサーバー）が存在しないことを確認
- Discordbot は `ClaudeBot#9398` という名前

---

### 3. DiscordにPlaywrightで自動ログイン

**ユーザーの指示**: 「あなたがやって」

Playwright MCP を使ってブラウザを操作開始。  
`https://discord.com/app` へ遷移 → ログイン画面 → ユーザーがQRコードでログイン完了。

ログイン後、DM一覧に **ClaudeBot** が表示されているのを確認。  
過去に `hi`（22:06）というメッセージを送信済みだったが、ボットからの返信なし。

---

### 4. ボットがオフラインの原因調査

`hello` というテストメッセージを ClaudeBot の DM に送信 → 返信なし・オフライン継続。

サーバーをテスト起動して原因を特定：

```
discord channel: login failed: Error [TokenInvalid]: An invalid token was provided.
```

**原因**: `.env` に保存されていたボットトークンが**無効（期限切れまたは不正）**だった。

---

### 5. Discord Developer Portal でトークンをリセット

Playwright で `https://discord.com/developers/applications` を開く。

1. **ClaudeBot** アプリケーションをクリック
2. 左メニューの **Bot** → **トークンをリセット** をクリック
3. 確認ダイアログ「Botのトークンをリセットしますか？」→ **実行します！** をクリック
4. **多要素認証（MFA）ダイアログ**が表示 → ユーザーが手動でパスワード入力・完了

新しいトークンが画面に表示される：
```
[DISCORD_BOT_TOKEN - 省略]
```

---

### 6. .env ファイルを新トークンで更新

```bash
echo 'DISCORD_BOT_TOKEN=[TOKEN]' \
  > ~/.claude/channels/discord/.env
chmod 600 ~/.claude/channels/discord/.env
```

---

### 7. 新トークンでの接続テスト

サーバーをテスト起動し、接続確認：

```
discord channel: gateway connected as ClaudeBot#9398
```

**接続成功！** トークンが有効であることを確認。

---

### 8. 次のステップ（未完了）

現在のセッション（`claude --channels plugin:discord@claude-plugins-official`）を**再起動**することで、新しいトークンでDiscordボットが本番起動する。

再起動後の手順：
1. ターミナルで `claude --channels plugin:discord@claude-plugins-official` を実行
2. Discord で ClaudeBot に DM を送る
3. ボットが返信する**ペアリングコード**（6文字）を取得
4. Claude Code セッションで `/discord:access pair <コード>` を実行
5. 承認後、DMからClaudeに話しかけられるようになる
6. セキュリティのため `policy allowlist` に切り替え推奨

---

## 技術的メモ

### Discord プラグインの仕組み

```
claude --channels plugin:discord@claude-plugins-official
    └── bun server.ts（MCP サーバーとして起動）
            └── Discord Gateway に接続（WebSocket）
                    └── DM受信 → Claude に転送 → 返信
```

- 設定ファイル: `~/.claude/channels/discord/.env`（トークン）
- アクセス制御: `~/.claude/channels/discord/access.json`（ポリシー・許可リスト）
- サーバーコード: `~/.claude/plugins/marketplaces/claude-plugins-official/external_plugins/discord/server.ts`

### アクセス制御の種類

| ポリシー | 説明 |
|----------|------|
| `pairing` | DM を送るとペアリングコードで認証（初期設定） |
| `allowlist` | 登録済み Discord ユーザーのみ許可（推奨・本番用） |
| `disabled` | 誰も使えない |

### 使われたツール

- **Playwright MCP**: ブラウザの自動操作（Discord ログイン・Developer Portal 操作）
- **Bash**: プロセス確認・ファイル操作・サーバーテスト起動

---

## トラブルシューティング記録

| 問題 | 原因 | 解決方法 |
|------|------|----------|
| ボットがオフライン | トークンが無効（`TokenInvalid`） | Developer Portal でトークンをリセット |
| `bun` プロセスが存在しない | トークンエラーでサーバーが起動直後に落ちていた | トークン更新後に再起動 |
| MFA が必要だった | Discord のセキュリティ設定 | ユーザーが手動でパスワード入力 |

---

*作成: Claude Code (claude-sonnet-4-6) / 2026-04-02*
