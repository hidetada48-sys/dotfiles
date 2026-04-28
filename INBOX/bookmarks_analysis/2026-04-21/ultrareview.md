# /ultrareview — クラウドでバグ検出エージェントを並列実行する新機能

## 基本情報

- **発表日：** 2026-04-22（@ClaudeDevs 公式アカウント）
- **ステータス：** Research Preview（CLI バージョン 2.1.86 以降）
- **利用条件：** Pro / Max ユーザー。5/5 まで3回無料。以後は変更サイズに応じて $5〜$20/回。

---

## 何をするものか

`/ultrareview` は Claude Code に追加された新しいコマンド。実行すると：

1. リポジトリの状態をパッケージ化してリモートサンドボックスにアップロード
2. クラウド上で**複数のレビューエージェントが並列**で変更を探索
3. 各エージェントが異なる観点（アプリロジック・エッジケース・セキュリティ・パフォーマンス）からレビュー
4. 結果が CLI または Desktop に自動で届く（所要時間：diff のサイズによって10〜20分）

---

## 推奨ユースケース（Anthropic 公式）

| ユースケース | 説明 |
|---|---|
| **認証フロー（auth）** | セキュリティ上のリスクが高い変更 |
| **データマイグレーション** | データ損失・整合性破壊のリスクがある変更 |
| **大規模リファクタリング** | 副作用が広範囲に及ぶ変更 |

→ 「マージ前の最終確認」としての位置づけ。

---

## 自分の環境での使い方

現在のプロジェクト（~/test2）でブランチに変更が積まれているときに実行する。

```bash
# Claude Code CLI から実行
/ultrareview
```

結果は自動でターミナルまたは Claude Desktop に届く。

---

## コスト感

| 変更サイズ | 推定コスト |
|---|---|
| 小〜中（PR単位） | $5〜$10 |
| 大（マイグレーション等） | $10〜$20 |

→ **5/5 まで3回無料**なので、今すぐ試して感触を掴むべき。

---

## 推奨アクション

1. `claude --version` で CLI バージョンが 2.1.86 以上か確認
2. 変更が積まれているブランチで `/ultrareview` を実行
3. 結果を確認し、検出精度・有用性を評価する
4. 5回の無料枠を使い切る前に、有料で使う価値があるか判断する

---

## 参考情報

- [Claude Code /ultrareview: the Bug-Hunting Agent Fleet in the Cloud](https://pasqualepillitteri.it/en/news/1301/claude-code-ultrareview-agents-cloud-2026)
- [Anthropic Introduces Agent-Based Code Review for Claude Code - InfoQ](https://www.infoq.com/news/2026/04/claude-code-review/)
- [Claude Code Ultrareview Hunts Bugs Before You Merge](https://everydayaiblog.com/claude-code-ultrareview-bug-hunting-agents/)
