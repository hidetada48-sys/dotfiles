# アプデ一覧MD作成までの記録（2026-03-27〜03-28）

収集日：2026-04-05
対象期間：2026-03-27〜2026-03-28
※会話ログはセッション終了後に消滅。残存する断片（コミット記録・memory・ファイル本体）を割愛・要約せず時系列に並べる。

---

## 前提：この作業に至るまでの経緯

3/11〜3/17にかけてXブックマーク自動収集システム（fetch_bookmarks.py）を開発・改修。
3/17時点での対応済み取得パターン：
- 通常ツイート本文 ✅
- X長文記事 ✅
- 通常ツイート + 引用通常ツイート ✅
- 通常ツイート + 引用X記事 ✅（3/17修正）
- 通常ツイート + 外部リンクカード ✅（3/17修正）

---

## 2026-03-27（金）22:52:42 — fetch_bookmarks.py大幅改修

### コミット情報

```
da393be  2026-03-27 22:52:42 +0900
fetch_bookmarks.pyを大幅改修：取得の安定性と柔軟性を向上

主な変更点:
- double-gotoバグ修正: 2回目のpage.goto()削除、wait_for_selectorで待機
- 通常モード: 処理済みIDが出たら自動停止（件数制限撤廃）
- --limitモード: 処理済みIDでも停止せずphase2でスキップ
- --from/--to: 日付範囲指定モードを新規追加
- 件数制限をforループ内でも厳密に制御
- スクロール継続判定をseen_ids（スキップ含む）ベースに変更
- フェーズ2で未処理分のみ詳細取得するよう最適化
```

変更ファイル：`scripts/fetch_bookmarks.py`（106行追加・37行削除）

### 主な差分内容

**double-gotoバグ修正**
```python
# 修正前：2回gotoするとDOMがリセットされて0件になる問題があった
page.goto('https://x.com/i/bookmarks', wait_until='domcontentloaded', timeout=60000)
time.sleep(3)

# 修正後：既にブックマークページにいるのでgoto不要、ツイート出現まで待機
try:
    page.wait_for_selector('[data-testid="tweet"]', timeout=15000)
except Exception:
    pass
```

**通常モードの停止ロジック変更**
```python
# 修正前：デフォルト25件で打ち切り
fetch_limit = max_bookmarks if max_bookmarks is not None else 25

# 修正後：処理済みIDが出たら自動停止（件数制限撤廃）
elif max_bookmarks is None:
    if tweet_id in processed_ids:
        reached_cutoff = True
        break
```

**--from/--toオプション追加**
```python
parser.add_argument('--from', dest='from_date', default=None,
                    help='取得開始日（期間指定モード）例: --from 2026-03-17')
parser.add_argument('--to', dest='to_date', default=None,
                    help='取得終了日（期間指定モード）例: --to 2026-03-20')
```

**スクロール継続判定の変更**
```python
# 修正前：収集件数ベース
if new_count == prev_count:

# 修正後：seen_ids（スキップ含む）ベース
if new_seen == prev_seen:
```

### この改修後の取得状況（test2 memoryより）

```
取得済み期間: 2026-03-17〜2026-03-27（約60件）
ファイル保存先: ~/.x-bookmark-sync/output/
Google Drive: X-Bookmarks-NotebookLM/ フォルダに同期済み
processed_ids: 60件記録済み
```

---

## 2026-03-28（土）10:32 — claude_code_updates_2026-03.md 作成

### 会話ログの状態

**消滅。** セッション終了後に会話ログは消える仕様のため、このセッションの会話内容は現存しない。

### 作業内容（断片から推定される事実）

- `~/.x-bookmark-sync/output/` にある3/17〜3/27のブックマークファイル（約57件）を読み込んだ
- 2026-03-17〜03-27のClaude Codeアップデートを抽出・整理した
- `~/dotfiles/INBOX/claude_code_updates_2026-03.md` として保存した（ファイルのタイムスタンプ：Mar 28 10:32）

### 作成されたファイルの構成

全13カテゴリ、268行：

1. 大型新機能（Channels・/schedule・Claude Code on the Web・PR自動修正・Auto Mode・claude-peers）
2. コマンド・スラッシュコマンド（15種以上）
3. CLIフラグ・環境変数
4. Skillsシステム（SKILL.mdフロントマター・人気サードパーティスキル一覧）
5. Hooksシステム（8種のフック・HTTPフック対応）
6. Subagents（対立検証パターン含む）
7. モデル変更（Opus 4.6デフォルト化・1Mトークン）
8. 定期実行の選択肢比較（cron/loop/schedule/GitHub Actions）
9. VS Code拡張機能の更新
10. パフォーマンス改善（74%削減・426KB削減等）
11. .claudeフォルダ構造（settings.jsonの3段階権限設計）
12. MCP連携の注意点（disabledMcpServers推奨）
13. 上級活用Tips（Stop Hook・検証フィードバックループ・Plan Mode等）

---

## 2026-03-29（日）21:17:16 — dotfilesにコミット

### コミット情報

```
675fd6c  2026-03-29 21:17:16 +0900
セキュリティ強化・スキル追加・設定更新

- settings.json: denyリスト追加（rm -rf, force push, .env読み書き禁止）
- settings.json: PostToolUse/PostCompactフック・disabledMcpServers追加
- CLAUDE.md: 公式ドキュメント確認ルール・作業完了定義を追加
- スキル追加: superpowers / planning-with-files / health
- scripts: post-tool-check.sh（.py/.json構文チェック）追加
- INBOX: claude_code_updates_2026-03.md 追加  ← このファイルが初めてgit管理下に
- skills-lock.json 追加
```

変更ファイル数：22ファイル、2671行追加

---

## 欠落している記録

| 期間 | 内容 | 状態 |
|---|---|---|
| 3/28 会話ログ | ブックマーク読み込み〜MD作成の全会話 | **消滅（セッション終了で削除）** |
| 3/27 会話ログ | fetch_bookmarks.py改修の全会話 | **消滅** |

---

*作成: Claude Code (claude-sonnet-4-6) / 2026-04-05*
