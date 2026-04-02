# Claude Code × Discord Channels 設定作業ログ
**日時:** 2026-04-01〜2026-04-02  
**目的:** Claude CodeとDiscordを連携させてスマホから遠隔操作できる環境を構築する

---

## 背景・前回からの引き継ぎ

前回セッション（2026-04-01以前）でDiscordペアリングまで完了していたが、MCPサーバーが古いキャッシュを持っていたため返信できていなかった。再起動後の動作確認が課題として残っていた。

**ペアリング済み情報:**
- senderId: `1111830326176653344`（saku392911）
- chatId: `1488887174723145998`

---

## 2026-04-01 作業ログ

### 動作確認（返信テスト）

Discordの最新メッセージを確認したところ、saku392911から「test」「ありがとう 届いたよ」「届かない？」などのメッセージが届いていた。

**返信テスト実行:**
```
送信: こんにちは！Claude Codeです。Discord連携のテスト返信です。正常に動作しています。
結果: 送信成功（id: 1488897281628573888）
```

→ **返信成功。Discord連携の動作確認完了。**

### 判明した構造的問題

ユーザーから「Discordからメッセージを送っても届かないし返信がない」との指摘。

調査の結果、以下の問題が判明：

- 私（Claude Code）が**能動的に確認しに行かないとメッセージに気づけない**
- Discord → Claude Codeへの「自動通知」がない状態
- つまり、ユーザーがこのセッションで「確認して」と言ったときだけ返信できる

---

## 2026-04-02 作業ログ

### 公式ドキュメントの確認

`~/.claude/plugins/marketplaces/claude-plugins-official/external_plugins/discord/` にある以下を読んだ：

- `README.md`
- `ACCESS.md`

**重要な発見：`--channels` フラグが必要**

README Step 6に明記されていた：
```bash
claude --channels plugin:discord@claude-plugins-official
```

このフラグ付きで起動しないとDiscordメッセージが届かない。フラグ付きで起動すると、Discordからのメッセージが `<channel>` タグとしてセッションに自動的に届く。

**その他の公式ドキュメント確認内容:**
- `download_attachment` でダウンロードされたファイルは `~/.claude/channels/discord/inbox/` に保存される
- access.jsonはメッセージ受信ごとに再読み込みされる（再起動不要）
- `DISCORD_ACCESS_MODE=static` で起動時固定も可能

### INBOXのアップデートまとめmd確認

`~/dotfiles/INBOX/claude_code_updates_2026-03.md`（3/28更新）を読んだ。

3/17〜3/27のClaude Codeアップデートが網羅されていた。Discord Channels関連の記載：

- **Channels機能**: v2.1.80以降で利用可能
- **起動フラグ**: `--channels`
- **完全無人運用**: `--dangerously-skip-permissions`（信頼できる環境限定）
- **Auto Mode**: `--enable-auto-mode`（安全分類器が判断）

### tmuxのインストール

Crostini環境にtmuxが未インストールだったためインストール：
```bash
sudo apt-get install -y tmux
# → tmux 3.3a-3 インストール完了
```

### Discord自動応答の仕組みを構築

**構成:**

```
~/discord-bot/
└── CLAUDE.md    # ボットの動作制限・ルールを記載

~/.claude/scripts/
├── discord-start.sh   # tmuxセッションで自動応答を起動
└── discord-stop.sh    # 停止スクリプト
```

**discord-start.sh の内容（要点）:**
```bash
tmux new-session -d -s "discord-bot" \
    "cd ~/discord-bot && claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions"
```

**起動コマンド:**
```bash
bash ~/.claude/scripts/discord-start.sh   # 起動
bash ~/.claude/scripts/discord-stop.sh    # 停止
tmux attach -t discord-bot                # 画面確認
```

### 起動・接続テスト

```bash
bash ~/.claude/scripts/discord-start.sh
# → "Listening for channel messages from: plugin:discord@claude-plugins-official"
# → 待機状態になったことを確認
```

Discordからsaku392911が送ったメッセージ（「hi」「何か動かしてみて」「このセッションの履歴確認して」）がtmuxセッションに届き、PC上で処理されて返信されていることを確認。

→ **接続テスト成功。自動応答が動作していることを確認。**

---

## 判明した課題・制限事項

### 課題1：セッションが分離している問題

**状況:**
- 手元のセッション（このClaude Code）でPC上の作業をしている
- discord-botセッション（tmux内）は**全く別の独立したセッション**

**問題:**
Discordから「このセッションの履歴確認して」と指示しても、discord-botセッションはPC手元セッションの作業内容を知らない。Discordの会話履歴しか見れない。

**解決策:**
最初から `--channels` 付きで1つのセッションとして起動する必要がある：
```bash
cd ~/my-project
claude --channels plugin:discord@claude-plugins-official
```
→ 手元作業もDiscord遠隔操作も**同一セッション**で行う

### 課題2：手元を離れるときの許可確認

`--channels` だけだと、遠隔操作時に許可確認が出て止まってしまう。

**解決策の選択肢:**

| フラグ | 安全性 | 用途 |
|---|---|---|
| `--dangerously-skip-permissions` | 低（全スキップ） | 完全無人・信頼環境限定 |
| `--enable-auto-mode` | 中（AI判断） | ほぼ無人・推奨 |
| なし | 高 | 手元作業時 |

---

## 理想的な運用フロー（結論）

```
1. リポジトリで作業開始（--channels付きで最初から起動）
   cd ~/my-project
   claude --channels plugin:discord@claude-plugins-official --enable-auto-mode

2. PCで手元作業（通常通りターミナルで会話）

3. 席を外すタイミングでスマホのDiscordに切り替え
   → 同一セッションなので作業文脈が共有されている

4. Discordから遠隔で続きの作業を指示

5. 戻ったらターミナルで続きを確認・操作
```

**起動の簡易コマンド（未実装・今後の課題）:**
```bash
# 「testリポジトリでchannelsで再起動して」と言うだけで↓を実行できるようにする
cd ~/test && claude --channels plugin:discord@claude-plugins-official --enable-auto-mode
```

---

## 未解決・今後の検討事項

1. **リポジトリ指定の起動スクリプト** — `discord-start.sh ~/my-project` でリポジトリ指定できるよう改良
2. **Crostini再起動後の自動復旧** — systemdが使えないため、ログイン時に自動起動する方法が必要
3. **このセッション（手元）がどこで動いているか** — 確認途中で中断
4. **`--dangerously-skip-permissions` の安全性** — allowlistにsaku392911のみが入っていることを確認済みだが、運用ポリシーの整理が必要

---

## 参考：関連ファイル一覧

```
~/.claude/plugins/marketplaces/claude-plugins-official/external_plugins/discord/README.md
~/.claude/plugins/marketplaces/claude-plugins-official/external_plugins/discord/ACCESS.md
~/.claude/channels/discord/access.json
~/discord-bot/CLAUDE.md
~/.claude/scripts/discord-start.sh
~/.claude/scripts/discord-stop.sh
~/dotfiles/INBOX/claude_code_updates_2026-03.md
```
