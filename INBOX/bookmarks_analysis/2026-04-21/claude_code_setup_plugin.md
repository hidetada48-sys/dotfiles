# claude-code-setup — Anthropic公式セットアップ診断プラグイン

## 基本情報

- **提供元：** Anthropic（公式プラグインリポジトリ `claude-plugins-official`）
- **インストール方法：** `/plugin install claude-code-setup@claude-plugins-official`
- **公式プラグインリポジトリ：** https://github.com/anthropics/claude-plugins-official

---

## 何をするものか

プロジェクトのコードベースをスキャンし、そのプロジェクトに最適なセットアップを提案するプラグイン。シニアエンジニアがリポジトリをレビューするレベルの精度で以下を分析・提案する：

| 診断対象 | 内容 |
|---|---|
| **Hooks** | どのイベントに自動処理を設定すべきか |
| **Skills** | どんな業務スキルを追加すべきか |
| **MCP Servers** | どの外部サービス連携が有用か |
| **Subagents** | 役割分担すべきタスクはあるか |
| **Slash Commands** | カスタムコマンドとして登録すべき操作はあるか |

---

## インストール方法（1行）

```bash
# Claude Code CLI 内で実行
/plugin install claude-code-setup@claude-plugins-official
```

インストール後、`「このプロジェクトに合う自動化を提案して」` と質問するだけで診断が始まる。

---

## 自分の環境での活用シナリオ

現在のプロジェクト（~/test2、~/dotfiles）で実行すると：

- **x-bookmark-weekly** など既存スキルとの重複・改善提案を得られる
- まだ未設定のMCP Server（Slack、Gmail等）の追加を提案される可能性
- Hooks の設定漏れを検出できる

---

## 公式プラグインエコシステムの補足

- Anthropicは `claude-plugins-official` リポジトリで公式プラグインを管理
- プラグインは Skills・アプリ統合・MCP Servers を束ねた「ワークフローのパッケージ」として提供
- `@` 記号で特定のプラグインやスキルを明示的に呼び出すことも可能

---

## 推奨アクション

1. `~/test2` プロジェクト内で `/plugin install claude-code-setup@claude-plugins-official` を実行
2. 診断結果を確認し、提案されたスキル・Hooks・MCPをリストアップ
3. 優先度をつけて段階的に適用する

---

## 参考情報

- [GitHub - anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)
- [Create plugins - Claude Code Docs](https://code.claude.com/docs/en/plugins)
- [Plugins for Claude Code and Cowork | Anthropic](https://claude.com/plugins)
