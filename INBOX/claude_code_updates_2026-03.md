# Claude Code 直近アップデート 網羅まとめ（2026年3月17日〜27日）

ブックマークファイル（~/.x-bookmark-sync/output/）の3/17以降57ファイルから抽出。

---

## 1. 大型新機能

### Channels（チャンネルズ）
- **スマホからPCのClaude Codeを遠隔操作**できる機能
- Discord / Telegram経由で双方向通信（MCPサーバー経由）
- **v2.1.80以降**で利用可能（`npm install -g @anthropic-ai/claude-code` で更新）
- 起動フラグ：`--channels`
- 6桁のペアリングコードで認証。危険な操作は確認あり
- 完全無人運用：`--dangerously-skip-permissions` フラグ（信頼できる環境限定）
- 組織利用：Admin settings → Claude Code → Channels から管理者が有効化
- **Proプラン（月額$20）の枠内で追加料金なし**

### /schedule コマンド（Cloud Trigger）
- **Anthropicのクラウド上でタスクを定期実行**。PCを閉じていても動き続ける
- セッション内で `/schedule` と打ち、リポジトリ・スケジュール・プロンプトの3点を指定するだけ
- **3日で自動失効**（安全装置として意図的な設計）
- 活用例：CI失敗の自動修正、ドキュメント定期更新・プッシュ、依存パッケージの自動アップグレードとPR提出、放置PRへの自動フラグ付け
- **Proプラン以上で追加費用なし**

### Claude Code on the Web
- ブラウザからClaude Codeを起動：`claude.ai/code`（research preview）
- Pro/Max/Team/Enterprise対応
- GitHubを接続してリポジトリ指定するだけでAnthropicのクラウドVM上で実行
- iOS/Androidアプリ対応（外出先からタスク開始・進捗確認可）
- `--remote` フラグでターミナルからウェブセッション開始、`teleport` でウェブセッションをローカルに引き込むことも可能
- ラップトップを閉じてもセッション継続

### PR自動修正（Auto-fix Pull Requests）
- CIが失敗 or レビューコメントが付くと**Claudeが自動で調査・修正・プッシュ**
- 有効化方法：ウェブ版Claude CodeのCIステータスバー「Auto-fix」を選択、またはモバイルで「watch this PR and fix any CI failures」と指示
- 明確な修正は自動実行、曖昧な指示は確認、重複イベントはスキップ
- GitHub上にはあなたのアカウント名で「from Claude Code」ラベル付きで投稿

### Auto Mode（自動承認モード）
- AIの安全分類器がアクションを自動判断してツール実行の許可確認をスキップ
- 有効化：`--enable-auto-mode` フラグ
- セッション中の切替：`Shift+Tab`
- `--dangerously-skip-permissions` との違い：Auto Modeは安全分類器が判断するため安全

### claude-peers（セッション間通信）
- 同一マシン上の複数のClaude Codeセッション間でメッセージをやり取り
- localhost:7899でブローカーデーモンが動作
- v2.1.80以降で利用可能

---

## 2. コマンド・スラッシュコマンド

| コマンド | 概要 |
|---|---|
| `/schedule` | クラウド上で定期タスク設定（PC不要） |
| `/loop 5m [指示]` | 指定間隔でプロンプトを繰り返し実行（ターミナルを閉じると停止） |
| `/effort low/medium/high/auto` | 思考の深度をその場で切り替え（○◐●で表示） |
| `/voice` | プッシュトゥトーク音声入力（20言語対応、3月に10言語追加） |
| `/color` | セッションのプロンプトバーに色を設定（並列セッション区別に便利） |
| `/rename` | セッション名をプロンプトバーに表示 |
| `/copy` | コードブロックをインタラクティブピッカーでコピー |
| `/config` | 設定変更（Esc=キャンセル、Enter=保存、Space=トグル） |
| `/model opusplan` | 計画フェーズはOpus・実装フェーズはSonnetに自動切替 |
| `/fast` | Opus 4.6を2.5倍速に |
| `/context` | コンテキスト消費ツールの特定・メモリ肥大化警告 |
| `/reload-plugins` | 再起動なしでプラグインをリロード |
| `/fork` | 会話をフォークして並列タスク実行 |
| `/rewind` | 前のチェックポイントに戻る |
| `/clear` | 会話履歴（コンテキスト）をリセット。再起動不要 |
| `/compact` | コンテキストを圧縮（リセットではなく要点だけ残す） |
| `ultrathink` | プロンプトに含めると1ターンだけhigh effort発動 |

---

## 3. CLIフラグ・環境変数

| フラグ/変数 | 概要 |
|---|---|
| `--channels` | Channels機能を有効化 |
| `--enable-auto-mode` | Auto Mode有効化 |
| `--bare` | hooks/LSP/プラグイン同期をスキップした軽量モード |
| `-n / --name` | 起動時にセッション名を設定 |
| `--remote` | ウェブセッションをターミナルから開始 |
| `--dangerously-skip-permissions` | 全許可をスキップ（完全無人運用） |
| `CLAUDE_CODE_DISABLE_CRON` | cronジョブを即時停止 |
| `ENABLE_CLAUDEAI_MCP_SERVERS=false` | claude.aiのMCPサーバーをオプトアウト |
| `ANTHROPIC_CUSTOM_MODEL_OPTION` | /modelピッカーにカスタムエントリを追加 |

---

## 4. Skillsシステム

- Skillsは「Claude Codeに特定の仕事のやり方を教えるマニュアル」
- SKILL.mdファイルにYAMLフロントマター＋マークダウン本文で定義
- Commands（手動）との違い：Skillsは会話の流れでClaudeが自動判断して呼び出す

### SKILL.md主要フロントマターフィールド

| フィールド | 概要 |
|---|---|
| `effort` | 思考深度（low/medium/high/max）をスキルごとに個別指定 |
| `model` | 使用モデル指定（例：sonnet/haiku） |
| `allowed-tools` | 使用できるツールを制限 |
| `user-invocable` | ユーザーが手動呼び出し可能か |
| `agent` | サブエージェント設定 |
| `hooks` | フック設定 |

### シェルインターポレーション
- SKILL.md内で `` !`コマンド` `` と書くとコマンド実行結果を自動注入

### Bundled Skills（同梱6種）
1. `/batch` — 大規模並列変更
2. `/simplify` — 3観点コードレビュー
3. `/loop` — 定期実行
4. `/debug` — セッションデバッグ
5. `/claude-api` — Anthropic SDKリファレンス自動ロード
6. `/review` — コードレビュー

### Skillsはオープン標準
- Cursor・Gemini CLI・Codex CLI等でも動作する「Agent Skills」オープン標準
- `npx skills add owner/repo` でインストール
- skills.sh（Vercel製）：公開6時間で2万インストール突破

### 人気サードパーティスキル

| スキル名 | インストール数 | 概要 |
|---|---|---|
| superpowers | ⭐109,607 | 出力品質底上げのメタスキル |
| planning-with-files | ⭐17,032 | 計画ファイルを先に書いてから実装するManus式ワークフロー |
| gogcli | ⭐6,500 | Gmail・カレンダー・Drive・ContactsをCLIから操作 |
| Understand-Anything | ⭐5,745 | コードベースをインタラクティブなナレッジグラフに変換 |
| trailofbits/skills | ⭐3,862 | セキュリティ監査自動化（Trail of Bits製） |
| playwright-skill | ⭐2,128 | Playwrightでブラウザ自動化 |
| mcp_excalidraw | ⭐1,531 | Excalidraw形式の図解をAIで生成 |
| claude-health | ⭐505 | CLAUDE.md・settings.json・スキル構成を6層で診断 |

---

## 5. Hooks（フック）システム

「Claude Codeが特定の動作をするタイミングで、自動的に別のコマンドを実行する仕組み」

| フック | 発火タイミング |
|---|---|
| `PreToolUse` | ツール実行前 |
| `PostToolUse` | ツール実行後 |
| `UserPromptSubmit` | メッセージ送信時 |
| `Stop` | Claude応答完了時（「テストが通るまで続行」強制に有効） |
| `PreCompact` | コンテキスト圧縮前 |
| `PostCompact` | コンテキスト圧縮後（新規追加） |
| `Notification` | 権限確認リクエスト |
| `Elicitation / ElicitationResult` | MCPサーバーがユーザー入力を求めるとき（新規追加） |
| `InstructionsLoaded` | CLAUDE.md読み込み時（新規追加） |

- **HTTPフック（新機能）**：シェルコマンドの代わりにURLへPOSTしてJSON応答を受け取る方式も対応

---

## 6. Subagents（サブエージェント）

- `~/.claude/agents/` または `.claude/agents/` にMarkdownファイルで定義
- 独自のシステムプロンプト・ツール制限（`tools:` フィールド）・モデル指定（`model:` フィールド）が可能
- 並列実行でメインエージェントのコンテキストを節約
- **対立検証パターン（Opponent Processor）**：賛否両方の視点のSubagentに議論させて判断精度向上

---

## 7. モデル変更

- **Opus 4.6がデフォルトモデルに**（Max/Team/Enterpriseプラン）
- **コンテキストウィンドウが100万トークンに拡大**（1M tokens）
- Opus 4/4.1は第一者APIから削除 → Opus 4.6に自動移行
- Opus 4.6のeffortデフォルトが high → **medium** に変更
- `/model opusplan`：計画はOpus（最上位品質）、実装はSonnet（高速）に自動切替

---

## 8. 定期実行の選択肢比較

| 方式 | AI関与 | PC不要 | 永続性 | 用途 |
|---|---|---|---|---|
| `cron` 単体 | なし | ローカル依存 | 無期限 | 定型処理 |
| `/loop` | あり | ローカル依存 | セッション内のみ | 一時監視 |
| `/schedule` | あり | クラウド実行 | **3日で失効** | 個人の定期実行 |
| `GitHub Actions + claude-code-action@v1` | あり | クラウド実行 | **無期限** | チームの長期運用 |

---

## 9. VS Code拡張機能の更新

- sparkアイコン：全セッションをフルエディタで一覧表示
- プランのマークダウンビュー＋コメント対応
- ネイティブMCPサーバー管理ダイアログ
- effortレベルインジケーター
- URIハンドラー：プログラム的に新タブを開く

---

## 10. パフォーマンス改善

- プロンプト入力リレンダリング **74%削減**
- 起動メモリ **426KB削減**
- Remote Controlポーリング **300分の1に削減**
- メモリリーク **15件以上修正**（ベースライン16MB削減）
- bashパーシングをネイティブモジュール化
- voice認識精度向上（regex/OAuth/JSON等の開発用語）
- @ファイルオートコンプリート高速化
- `--worktree` 起動パフォーマンス改善

---

## 11. .claudeフォルダ構造（現在の構成）

```
your-project/
├── CLAUDE.md               # チーム指示書（200行以内推奨）
├── CLAUDE.local.md         # 個人の上書き設定（自動gitignore）
└── .claude/
    ├── settings.json       # 権限・設定（git管理）
    ├── settings.local.json # 個人の権限上書き（gitignore）
    ├── commands/           # カスタムスラッシュコマンド
    ├── rules/              # CLAUDE.mdの分割管理（pathsフィールドで特定パスのみ適用）
    ├── skills/             # 自動起動ワークフロー
    └── agents/             # 専門サブエージェント

~/.claude/
├── CLAUDE.md               # グローバル指示書（全プロジェクト共通）
├── settings.json
├── commands/ / skills/ / agents/  # 個人用（全プロジェクト共通）
└── projects/               # セッション履歴・自動記憶
```

### settings.jsonの3段階権限設計

```json
{
  "permissions": {
    "allow": ["Bash(npm run *)", "Read", "Write", "Edit"],
    "deny": ["Bash(rm -rf *)", "Read(./.env)"]
  }
}
```
- `allow`：確認なしで実行
- `deny`：何があっても完全ブロック
- どちらにもない：実行前に確認を求める

---

## 12. MCP連携の注意点

- MCPを多く設定するとコンテキストを大幅に圧迫（200kトークンが70kになることも）
- 推奨：設定は20〜30個、有効化は10以下、アクティブツールは80以下
- `disabledMcpServers` でプロジェクトごとに管理
- **MCP elicitation（新機能）**：MCPサーバーがフォームやURLでユーザー入力を要求できる仕組み

---

## 13. 上級活用Tips

- **Stop Hook**で「テストが通るまで作業継続」を強制 → 確率的なモデルから確定的な成果を引き出す
- **検証フィードバックループ**：Claudeに検証手段を与えると最終品質が**2〜3倍向上**
- **Plan Mode**（`Shift+Tab`）：計画確定後にauto-acceptで一発実装
- **並列セッション**：Anthropic社員はローカル5セッション＋リモート5〜10セッションを同時運用
- **コンテキストエンジニアリング**：プロンプト設計よりも「渡す前提情報の設計力」が成果を決める
- **Claude Code使いこなし5段階**：Lv.3（Agent設計とSkills構築）から質が大きく変わる
