# ブックマーク精読・調査レポート 2026/04/07〜04/13

**作成日:** 2026-04-15  
**対象ファイル:** `~/test2/bookmarks/bookmarks_0407-0413.md`（23件）  
**調査方法:** ツイート本文精読 + Web検索で情報密度を補完

---

## 現在の環境（調査時点）

**settings.json の状態（抜粋）:**
- `effortLevel` → **未設定**（デフォルト `medium`）
- `showThinkingSummaries` → **未設定**
- RTKフック → 設定済み（Linuxのみ有効）
- basic-memory MCP → 設定済み
- CLAUDE.md → 55行（余裕あり）

**既存スキル:** brainstorming / health / planning-with-files / using-superpowers / x-bookmark-to-notebooklm / x-bookmark-weekly

---

## 提案一覧

### ① `effortLevel: "high"` を settings.json に追加 ★最優先

**背景:**  
ブックマーク中で最多言及。「最近Claudeが雑になった」の原因は、デフォルト思考予算が `medium` に変更されたこと。GitHub issue #42796 で6,852セッション・17,871の思考ブロックを実測分析して確認済み。複雑なタスクで「調査より先に編集に飛びつく」現象が発生する。

**対策:**
```json
"effortLevel": "high"
```

**既知のバグ:** 新セッション起動時に設定が無視されることがある（issue #39133）。  
**完全対策:** CLAUDE.md にも「複雑なタスク前は `/effort high` を実行する」と明記する。

**情報源:** @showheyohtaki, @MakeAI_CEO, @kawai_design, @kzkhykw

---

### ② `showThinkingSummaries: true` を settings.json に追加 ★最優先

**背景:**  
Claudeの思考過程を可視化する設定。`effortLevel: high` とセットで使う。浅い思考のままいきなり編集に入っているときに気づけるようになる。

```json
"showThinkingSummaries": true
```

**情報源:** @showheyohtaki（@PawelHuryn 引用）

---

### ③ CodeX plugin（OpenAI）の導入

**概要:**  
OpenAIが公式リリースしたClaude Code用プラグイン（Apache 2.0・無料）。ChatGPT無料アカウントまたはOpenAI APIキーで使用可。Node.js 18.18以上が必要。

**インストール:**
```
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/codex:setup
!codex login
```

**できること:**
| コマンド | 内容 |
|---------|------|
| `/codex:review` | Claudeのコードを異なるモデルでレビュー（バグ見逃し防止） |
| `/codex:adversarial-review` | 実装判断・トレードオフへの批判的レビュー |
| `/codex:rescue` | Claudeが詰まったらCodeXにサブエージェントとして引き継ぎ |
| レビューゲート | Claudeの出力をCodeXが自動チェック。問題があれば完了をブロック |

**情報源:** @masahirochaen  
**公式リポジトリ:** https://github.com/openai/codex-plugin-cc

---

### ④ caveman スキルの導入（トークン削減）

**概要:**  
穴居人語風の簡潔出力でClaude自身の応答トークンを削減するスキル。RTKはコマンド出力のフィルタリング、cavemanはClaude応答の短縮という補完関係にある。

**実測値:**
- 応答トークン: 1,214 → 294（65%削減）
- セッション全体: 4〜10%削減（応答は全体の約25%のため）

**強度レベル:** lite / full（推奨） / ultra / wenyan（漢文風）

**インストール:**
```bash
# dotfilesに追加する場合
mkdir -p ~/dotfiles/claude/skills/caveman
# SKILL.md を https://github.com/JuliusBrussee/caveman から取得
```

**情報源:** @saeroyi_ican  
**公式リポジトリ:** https://github.com/JuliusBrussee/caveman

---

### ⑤ `rules/` ディレクトリ＋`mistakes.md` の導入

**背景:**  
現在のCLAUDE.mdは55行（余裕あり）。ただし将来的なルール増加への設計として参考になる。200行超えるとコンテキスト圧迫でルール遵守率が低下する実測報告あり。

**構成案:**
```
~/.claude/rules/
├── git-workflow.md    # Gitルール（現CLAUDE.mdのGitセクションを移動）
├── mistakes.md        # やらかしログ（新規）
```

**`mistakes.md` の役割:**  
過去にやらかしたパターンを記録し再発防止に使う。プロジェクト横断で効果あり。auto-memoryのfeedbackと役割が近いが、こちらはClaude自身が読むルールファイルとして機能する。

**情報源:** @okuyama_ai_, @ai_jitan

---

### ⑥ Monitor ツールの活用

**概要:**  
Claude Code v2.1.98（2026-04-09）で追加。インストール不要の組み込みツール。バックグラウンドスクリプトを自動生成してstdoutの各行をリアルタイムでClaudeに通知する仕組み。

**仕組み:**
```
Claude → スクリプト自動生成 → バックグラウンド実行 → stdout各行がイベントとして返ってくる
```

**活用シーン:**
- `x-bookmark-weekly` systemdサービスのリアルタイムログ監視
- GDriveアップロード完了の検知
- git pull後の差分検知
- PRのCIステータス変化の監視

**使い方:** 「`Monitor ツールを使って〇〇を監視して`」と指示するだけでスクリプトを自動生成してくれる。

**情報源:** @claudecode_lab  
**公式ドキュメント:** https://code.claude.com/docs/en/tools-reference

---

### ⑦ X公式MCPサーバー（xmcp）

**概要:**  
XがMCPサーバーを公式リリース。Claude CodeからXへの投稿・検索・分析・リプライがターミナル完結になる。

**主な機能:**
- 投稿・スレッド投稿・下書き確認
- キーワード検索・バズ投稿抽出・トレンド取得
- インプレッション・エンゲージメント率確認

**必要なもの:** X Developer APIキー（取得時に5ドルチャージが必要）

**コスト:** 投稿読み取り$0.005/件、コンテンツ作成$0.010/件（毎日10ポスト≒500円/月）

**情報源:** @y_ruo1（引用: @kkk_cun）

---

## 今週のブックマーク全体傾向

| テーマ | 件数 | 注目度 |
|--------|------|--------|
| 思考予算（effortLevel）問題と対策 | 4件 | ★★★ 複数アカウントが独立して言及 |
| Skills解説・活用 | 5件 | ★★★ エコシステムが急拡大中 |
| Claude Managed Agents | 3件 | ★★★ 「エージェント自作時代の終焉」論調 |
| CodeX連携 | 1件 | ★★ 公式プラグイン・即実行可能 |
| Monitor ツール | 1件 | ★★ v2.1.98から使える |
| X MCP | 1件 | ★ 用途次第 |
| 情報収集自動化 | 1件 | ★★ x-bookmark-weeklyと方向性が一致 |

### 注目トレンド

**Claude Managed Agents の登場**  
Anthropicが本番インフラ込みのエージェント基盤を公開。「プロトタイプからローンチまで数日」。複数の投稿で「エージェントオーケストレーション系スタートアップを陳腐化させた」と言及されており、AIエージェント開発の転換点として認識されている。

**Skillsエコシステムの急拡大**  
skills.sh（Vercel）が公開6時間で2万インストール。トップスキルが7万2500インストール超。1,300以上のスキルが公開されているリポジトリも存在。Agent Skillsはオープン標準としてClaude Code以外でも動くようになっている。

**情報収集パイプラインという設計思想**  
@beku_AI が詳細に解説。「情報源の選定→フィルタリング基準→出力フォーマット→実行スケジュール」の4要素を設計してAIに実行させる考え方。x-bookmark-weeklyの設計と完全に一致しており、現在の仕組みは正しい方向にある。

---

## 即実行リスト（優先順）

- [ ] ① `effortLevel: "high"` を settings.json に追加
- [ ] ② `showThinkingSummaries: true` を settings.json に追加
- [ ] ③ CodeX plugin 導入（OpenAIアカウントがあれば）
- [ ] ④ caveman スキル追加（RTKと補完運用）
- [ ] ⑤ `mistakes.md` を `~/.claude/rules/` に作成
- [ ] ⑥ Monitor ツールを次の監視タスクで試す
- [ ] ⑦ X MCP（用途が出てきたら）
