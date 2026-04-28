# Claude Design — Anthropicの新デザインツール（2026-04-17 リリース）

## 基本情報

- **リリース日：** 2026-04-17（Anthropic Labs）
- **使用モデル：** Claude Opus 4.7（高解像度ビジョン対応）
- **料金：** Pro / Max / Team / Enterprise 加入者は追加料金なし
- **公式情報：** https://www.anthropic.com/news/claude-design-anthropic-labs

---

## 何ができるか

対話ベースで以下を生成する：

| 生成物 | 説明 |
|---|---|
| **ランディングページ（LP）** | HTML/CSS プロトタイプとして出力 |
| **スライド / ピッチデック** | PDF・PPTX・URL・Canva エクスポート |
| **プロポーザル / 提案書** | ビジネス文書形式 |
| **デザインモック** | クリック可能な動的プロトタイプ |

---

## GPT Image 2 との組み合わせワークフロー

ブックマーク内で多数紹介されていた実践的な組み合わせ：

```
1. ChatGPT でGPT Image 2 を使って画像素材を生成
   （2Kで日本語テキストも崩れない）
   ↓
2. 生成画像を Claude Design に渡して「このデザインでLP作って」
   ↓
3. HTML / PPTX / PDF で出力
```

**コスト感：** GPT Image 2 は1枚約0.25ドル（約38円）。1LP分で$3〜5程度。

---

## Claude Design vs Codex の違い（ブックマーク内比較分析より）

| 比較軸 | Claude Design | Codex |
|---|---|---|
| 統合度 | デザインフェーズのみ。コードとの分断あり | コード・ブラウザ・画像生成が1アプリ内完結 |
| エクスポート | Canva・PPTX・HTML | そのまま実装・デプロイ可能 |
| 修正フロー | 再度 Claude Design で修正 → エクスポート | In-app ブラウザでコメント→即修正 |
| 対象ユーザー | デザイン不慣れな非エンジニア | エンジニア・本格LP制作者 |

→ **非エンジニアが「デザイナーに近いアウトプット」を出す橋渡しとして最強クラス**。本格開発はCodexが優位。

---

## Claude Designの実績事例（ブックマークより）

- 鎧兜3Dワイヤーフレーム・フラクタル数学アート等を1行指示で生成（@MakeAI_CEO）
- 18分でアニメーション付きWebサイト（Liquid Glass UI + 動画背景）を完成（@SuguruKun_ai）
- 2時間程度で動画付きWebサイトをAIのみで構築（@Shin_Engineer）

---

## DESIGN.md との連携（おまけ）

Google が公式オープンソース化した `DESIGN.md` フォーマット（色・タイポ・スペーシングをMarkdownで記述）を Claude Code / Claude Design が自動読み込みする。一度作成すると全プロジェクトでブランド統一が実現できる。

---

## 推奨アクション

1. `claude.ai/design` にアクセスして Claude Design を試す（Pro加入者なら追加料金なし）
2. GPT Image 2 で素材画像を生成してClaude Designに渡すワークフローを1回試す
3. DESIGN.md を作成してdotfilesに配置し、Claude Code/Designでの自動読み込みを確認する

---

## 参考情報

- [Introducing Claude Design by Anthropic Labs](https://www.anthropic.com/news/claude-design-anthropic-labs)
- [Anthropic launches Claude Design, a new product for creating quick visuals - TechCrunch](https://techcrunch.com/2026/04/17/anthropic-launches-claude-design-a-new-product-for-creating-quick-visuals/)
- [Claude Design vs GPT Images 2.0: Two Different Bets on AI-Assisted Design | MindStudio](https://www.mindstudio.ai/blog/claude-design-vs-gpt-images-2)
- [What Claude Design is actually good for (and why Figma isn't dead, yet)](https://www.lennysnewsletter.com/p/what-claude-design-is-actually-good)
