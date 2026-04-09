# Xブックマーク整理 2026/3/27〜3/30

## 期間サマリー

- **対象期間：** 2026年3月27日〜3月30日
- **総ブックマーク数：** 15件
- **主なテーマ：** Claude Codeの新機能（Web版PR自動修正・スケジューラー・Computer Use）、フォルダ構造設計・スキル管理のベストプラクティス、Claude Coworkのプロジェクト機能追加、AIエージェントによるブラウザ自動化
- **カテゴリ別件数：**
  - Claude Code 新機能・機能解説：6件
  - Claude Code 設定・運用ベストプラクティス：5件
  - Claude Code ユースケース・活用事例：2件
  - Claude Cowork：1件
  - AIエージェント・開発ツール：1件

---

## カテゴリ1：Claude Code 新機能・機能解説

---

### Claude Code Web版 — PR自動修正がクラウド対応

- **投稿者：** @masahirochaen
- **日時：** 2026-03-27 00:44:35
- **URL：** https://x.com/masahirochaen/status/2037329903516110983

**ツイート本文（全文）：**

【速報】Claude Codeから新機能。PR自動修正がクラウド対応

PC起動せずに自動レビューは便利だな…

・CI失敗を検知→自動修正→常にグリーン維持
・レビューコメント自動対応
・Web/モバイルからPR登録するだけ、PCは不要
・GitHub Appとauto-merge設定で全自動マージ

**外部リンク内容（全文）：** https://code.claude.com/docs/en/claude-code-on-the-web#auto-fix-pull-requests

Claude Code on the web is currently in research preview.

What is Claude Code on the web?
Claude Code on the web lets developers kick off Claude Code from the Claude app. This is perfect for:
Answering questions: Ask about code architecture and how features are implemented
Bug fixes and routine tasks: Well-defined tasks that don't require frequent steering
Parallel work: Tackle multiple bug fixes in parallel
Repositories not on your local machine: Work on code you don't have checked out locally
Backend changes: Where Claude Code can write tests and then write code to pass those tests
Claude Code is also available on the Claude app for iOS and Android for kicking off tasks on the go and monitoring work in progress.
You can kick off new tasks on the web from your terminal with --remote, or teleport web sessions back to your terminal to continue locally. To use the web interface while running Claude Code on your own machine instead of cloud infrastructure, see Remote Control.

Who can use Claude Code on the web?
Claude Code on the web is available in research preview to:
Pro users
Max users
Team users
Enterprise users with premium seats or Chat + Claude Code seats

Getting started
Visit claude.ai/code
Connect your GitHub account
Install the Claude GitHub App in your repositories
Select your default environment
Submit your coding task
Review changes in diff view, iterate with comments, then create a pull request

How it works
When you start a task on Claude Code on the web:
Repository cloning: Your repository is cloned to an Anthropic-managed virtual machine
Environment setup: Claude prepares a secure cloud environment with your code, then runs your setup script if configured
Network configuration: Internet access is configured based on your settings
Task execution: Claude analyzes code, makes changes, runs tests, and checks its work
Completion: You're notified when finished and can create a PR with the changes
Results: Changes are pushed to a branch, ready for pull request creation

Review changes with diff view
Diff view lets you see exactly what Claude changed before creating a pull request. Instead of clicking "Create PR" to review changes in GitHub, view the diff directly in the app and iterate with Claude until the changes are ready.
When Claude makes changes to files, a diff stats indicator appears showing the number of lines added and removed (for example, +12 -1). Select this indicator to open the diff viewer, which displays a file list on the left and the changes for each file on the right.
From the diff view, you can:
Review changes file by file
Comment on specific changes to request modifications
Continue iterating with Claude based on what you see
This lets you refine changes through multiple rounds of feedback without creating draft PRs or switching to GitHub.

Auto-fix pull requests
Claude can watch a pull request and automatically respond to CI failures and review comments. Claude subscribes to GitHub activity on the PR, and when a check fails or a reviewer leaves a comment, Claude investigates and pushes a fix if one is clear.
Auto-fix requires the Claude GitHub App to be installed on your repository. If you haven't already, install it from the GitHub App page or when prompted during setup.
There are a few ways to turn on auto-fix depending on where the PR came from and what device you're using:
PRs created in Claude Code on the web: open the CI status bar and select Auto-fix
From the mobile app: tell Claude to auto-fix the PR, for example "watch this PR and fix any CI failures or review comments"
Any existing PR: paste the PR URL into a session and tell Claude to auto-fix it

How Claude responds to PR activity
When auto-fix is active, Claude receives GitHub events for the PR including new review comments and CI check failures. For each event, Claude investigates and decides how to proceed:
Clear fixes: if Claude is confident in a fix and it doesn't conflict with earlier instructions, Claude makes the change, pushes it, and explains what was done in the session
Ambiguous requests: if a reviewer's comment could be interpreted multiple ways or involves something architecturally significant, Claude asks you before acting
Duplicate or no-action events: if an event is a duplicate or requires no change, Claude notes it in the session and moves on
Claude may reply to review comment threads on GitHub as part of resolving them. These replies are posted using your GitHub account, so they appear under your username, but each reply is labeled as coming from Claude Code so reviewers know it was written by the agent and not by you directly.

Moving tasks between web and terminal
You can start new tasks on the web from your terminal, or pull web sessions into your terminal to continue locally. Web sessions persist even if you close your laptop, and you can monitor them from anywhere including the Claude mobile app.
Session handoff is one-way: you can pull web sessions into your terminal, but you can't（以下省略）

---

### Claude Code 定期実行まとめ — /schedule・/loop・cron・GitHub Actionsの使い分け

- **投稿者：** @masahirochaen
- **日時：** 2026-03-27 10:02:04
- **URL：** https://x.com/masahirochaen/status/2037470198840938565

**ツイート本文（全文）：**

【保存版】Claude Code 定期実行まとめ /schedule・/loop・cron・GitHub Actions、結局どれを使えばいい？

目次
「Mac mini要らないじゃん」と思った話
結局、何が違うのか——2軸で整理する
cron——タイマー単体 + Claude Code で「考える自動化」へ
/loop——「今だけ」監視したいときの手札
/schedule（Cloud Trigger）——PCを閉じても動く、これが本命
GitHub Actions + Claude Code——チームの最終解
8項目で比較する
cronと /schedule、何が本質的に違うのか
GitHub Actionsはどう使う？
選び方まとめ
失敗しやすいパターン
まとめ

1. 「Mac mini要らないじゃん」と思った話
3月21日に /schedule の発表を見て、最初に思ったのがこれだった。
「Mac mini要らないじゃん。メインPCを起動させる必要がないので、独立業務はGitHub経由でずっと自動実行できる」

従来のClaudeは対話型であり、セッション内でのみ動作する。Claude Codeの /loop コマンドもセッション限定で、ターミナルを閉じると同時にタスクは消える設計だった。

/schedule はその制約を取り除き、クラウド上で継続実行される。設定はリポジトリ・スケジュール・プロンプトの3点を指定するだけ。

CI失敗の自動修正、ドキュメントの定期更新などがPC起動なしに動き続ける。

cronと何が違うかというと、cronは「この時間にこのコマンドを起動する」機械的な仕組みで、CIが失敗しても記録するだけ。

/schedule はClaudeが失敗の内容を読んで修正コードを書いてコミットするところまで完結させる。

「定時起動」ではなく「定時エージェント実行」と捉えると近い。

ただ、繰り返しタスクは作成から3日で自動失効とのことで要注意。

実際にそう投稿したら9万インプレを超えた。それだけ「PC常時起動問題」を抱えていた人が多かったんだと思う。
まあ、何がそんなに刺さったかというと「PCを閉じても動く」という一点だ。今まで定期実行しようとすると、サーバーを借りるかMac miniを常時稼働させるか、cronを設定するかしかなかった。それがコマンド1行で解決するという話なので、反応が大きかったのも納得できる。
ただ、/schedule だけ知っておけばいいかというとそうでもない。/loop も cron も GitHub Actions も、それぞれ設計思想が根本的に違う。
「全部 /schedule でいい」とはならないので、きちんと整理しておく。

2. 結局、何が違うのか——2軸で整理する
定期実行の手法は「AIが関与するか」と「PCが必要か」の2軸で分けると頭が整理される。
AIなし × ローカル依存が cron。AIあり × ローカル依存が /loop。AIあり × クラウド実行が /schedule。AIなし × クラウド実行が GitHub Actions。
この2軸を理解するだけで、後はほぼ迷わない。「AIに判断させたいか」「PCの電源状態に依存したくないか」——この2点を先に自分に問いかけてから手法を選ぶと、迷いが大幅に減る。

3. cron——タイマー単体 + Claude Code で「考える自動化」へ
まず前提として押さえておく。cron 自体にAIはない。
Cron は時計係だ。「この時間になったら、これを実行して」と言うだけで、中身は何も理解しない。バックアップ、ログのローテーション、定期的なファイル削除——こういった「毎回同じことをする処理」にはcron単体で十分だ。シンプルで信頼性が高く、期限もない。
ただ CIが失敗してもログに「失敗」と記録するだけで、原因の分析も修正も全部人間の仕事になる。cronは起動するだけで、その先は何もしない。「考える」という処理をcronに求めるのが間違いだ。
では「cronでAI自動化してます」という話は何なのか。あれはcronが起動した先に Claude Code が動いているという構造だ。AIを担当しているのは Claude Code であって、cronはただのトリガーにすぎない。
この組み合わせが強い。cronが「7:00になった、起動しろ」と言い、Claude Codeが起動されてプロンプトを読み、データを集計・分析・文章化し、MCP（Slack等）経由で結果を送信する。3ステップの役割分担だ。
通常の Cron ジョブ（Python スクリプト等）は固定コードを毎回同じように実行するだけだが、Claude Code が加わると「毎回考えて実行する」に変わる。データの変化に応じてコメントや警告のトーンを変えたり、エラーの原因を読んで修正コードを書いたりといったことが、プロンプトを書くだけで実現できる。コードを変えなくても、プロンプトを更新するだけで挙動が変わる。

4. /loop——「今だけ」監視したいときの手札
Claude Codeのセッション内だけで動く一時的なスケジューラー。/loop 5m CIのステータスを確認して、失敗していたら内容をまとめて と入力するだけで、Claudeが5分ごとに確認・報告を繰り返してくれる。
自然言語で指示できる点がcronとの最大の違いで、cron式を書く必要がなく、指示内容の調整もその場でできる。デプロイの進捗監視、PR の一時チェック、セッション中の繰り返し作業に向いている。
ただしターミナルを閉じた瞬間に消える。セッション内最大50タスクという制限もある。「今だけ動けばいい」という用途専用の道具で、翌日も動かし続けたい処理には向かない。

5. /schedule（Cloud Trigger）——PCを閉じても動く、これが本命
Claude CodeのPMであるNoah Zweben氏が2026年3月24日に発表した新機能。設定はシンプルで、セッション内で /schedule を入力し、
①リポジトリ 
②スケジュール 
③プロンプト
の3点を指定するだけ。あとはAnthropicのクラウドが引き受けてくれる。
Anthropic社内での実際の活用例として、CIの失敗を自動検出して修正コードを書いてコミットする、ドキュメントの定期更新とプッシュ、パッチレベルの依存パッケージを毎週月曜に自動アップグレードしてPR提出、2日以上放置されているPRにフラグを立てるといったケースが挙げられている。
ひとつ注意点として、繰り返しタスクは作成から3日で自動失効する。これはバグではなくAnthropicによる意図的な安全装置で、忘れられたタスクの暴走やコスト超過を防ぐ設計だ。

6. GitHub Actions + Claude Code——チームの最終解
GitHubのCI/CDプラットフォームのスケジュールトリガーで Claude Code CLI を呼び出す構成だ。スケジュール管理は Actions、AI判断・実行は Claude Code という役割分担になる。
Cloud Trigger との違いは3点。無期限稼働（3日失効がない）、チームで設定を共有できる（YAMLをリポジトリで管理）、既存のCI/CDパイプラインに統合できる——この3点だ。
設定コストはかかるが、一度作れば完全放置できる。長期運用・チーム運用が前提なら、これが最も安定した構成になる。

7. 8項目で比較する
全部に丸がつく手法はない。そこが重要で、「これ一択」を探そうとすると必ず詰まる。AIの判断が要るかどうか、PCを閉じても動かしたいかどうか、チームで使うかどうか——この3点を先に決めてから比較表を見ると、自分の用途に合う手法がすぐ絞れる。

8. cronと /schedule、何が本質的に違うのか
見た目は同じ「定期実行」だけど、解決しようとしている課題のレベルが根本的に違う。
cronがやるのは「この時間にこのコマンドを起動する」ことだ。CIが失敗したとき、cronが記録するのは「失敗した」という事実だけ。なぜ失敗したか、どう直すかは人間が見に行く必要がある。cronには「読む」「判断する」「修正する」という概念がそもそも存在しない。
/schedule がやるのは「この時間に、この目的でClaudeを動かす」ことだ。Claudeが失敗ログを読んで、原因を特定して、修正コードを書いてコミットするところまで完結する。
以前、OpenClawが「毎週月曜の1週間AIニュースまとめを日曜の夜に勝手に作ってくれた」という投稿をした。X投稿や購読している海外メルマガ、ネットの情報を自動収集して、記事化→ファイル保存まで完了していた。これが /schedule の設計思想に近い。cronではこれは絶対に無理で、「情報を集めて何が重要かを判断して記事を書く」という部分がAIでないと成立しない。
一言で言うと、cronは「定時起動装置」で、/schedule は「定時エージェント実行装置」だ。

9. GitHub Actionsはどう使う？
以下の条件がひとつでも当てはまるなら、GitHub Actionsが自然な選択になる。
チームで共有したい場合、cronはローカル設定で個人依存になりやすく、/schedule の3日失効は管理が煩雑だ。GitHub Actionsはリポジトリにコードとして定義されるので、バージョン管理もできてチーム全員が設定を把握できる。誰かが退職・異動しても設定が消えることがない。
/schedule の3日失効が運用の邪魔になる場合、長期稼働が必要なタスクを3日ごとに再設定するのは持続しない。GitHub Actionsなら一度設定すれば無期限で動き続ける。
Claude Codeと組み合わせる場合、anthropics/claude-code-action@v1 を使うことで、スケジュール管理はActions、AI自律実行はClaude Codeという理想的な役割分担が実現できる。これが現時点で「無期限 × クラウド × AI判断」の3条件を同時に満たす唯一の構成だ。

10. 失敗しやすいパターン
/loop を使ったらPCを閉じてタスクが消えた——/loop はセッション限定の設計なので、PC不要で動かしたいなら /schedule を使う。
Cloud Trigger が3日後に突然止まった——3日の有効期限が仕様だ。長期運用ならカレンダーに「2日後に再設定」のリマインダーを入れるか GitHub Actionsへの移行を検討する。
cronを使ったがCI失敗に気づかなかった——cronは実行するだけで、判断・修正は人間の仕事だ。AIに対処させたいなら Claude Code を組み合わせる構成に変える。
「cronにAIが入っている」と思って使い始めた——cronにAIはない。AI部分を担うのはClaude Codeだ。この誤解が一番多いパターンで、動作の設計思想を根本から変える必要がある。

11. まとめ
「Mac mini要らないじゃん」と書いたのが3月21日で、9万インプレを超えた。それだけPC常時起動問題を抱えていた人が多かったということだろう。
ただその前提として押さえておきたいのが「cronにはAIがない」という点だ。cronはタイマーで、AIを担うのはClaude Codeだ。この役割分担を理解した上で手法を選ぶと、「思った通りに動かない」という事態を防げる。
選び方をシンプルにまとめるとこうなる。今すぐ試したいなら /schedule、PC閉じても永続稼働させたいなら GitHub Actions + Claude Code、今だけ監視したいなら /loop、AIの判断が不要な定型処理なら cron 単体で十分だ。
「AIに定期作業を委任する」インフラがコマンド1行で整う時代になってきた。cronという古い仕組みと Claude Code という新しいAIが組み合わさって、自動化の水準が一段引き上げられている。

（外部リンクなし・本文内に全内容含む）

---

### Claude Code × MCP 連携設定6カテゴリー

- **投稿者：** @masahirochaen
- **日時：** 2026-03-27 16:02:02
- **URL：** https://x.com/masahirochaen/status/2037560786378530929

**ツイート本文（全文）：**

私が使っている「Claude Code × MCP」の連携設定。
よければ参考にしてください！！

MCP連携を6カテゴリーに整理しました

 開発支援
・GitHub, Figma, Playwright
・コード生成〜デバッグまで全部AI

 デザイン
・Canva, Excalidraw, Mermaid
・構成図もUIもClaude Codeから直接生成

 ドキュメント
・Notion, Google Drive, Sheets
・要件定義・マニュアル・集計の読み書きを自動化

 コミュニケーション
・Gmail, Slack, Discord, Calendar
・返信・要約・スケジュール調整もClaude Codeが動く

 会計・営業
・freee, Salesforce, Ahrefs
・バックオフィスからSEO分析までカバー

 ブラウザ
・Chrome DevTools, Playwright, Firecrawl
・スクレイピング・E2Eテスト・デバッグ自動化

Claude CodeはMCPで外部サービスと繋げて初めて真価が発揮するかと思います。

（外部リンクはニコニコ生放送のページのため省略）

---

### Claude Codeのブレインストーミングスキル（brainstorming）

- **投稿者：** @09pauai
- **日時：** 2026-03-29 00:38:28
- **URL：** https://x.com/09pauai/status/2038053140080308446

**ツイート本文（全文）：**

5. ブレインストーミングスキル（brainstorming）

いきなりコードを書かせる前に、Claude Codeが「何を作るか」を一緒に整理してくれるスキル。
質問を1つずつしながら設計を詰めてくれるので、やり直しが減って作業効率が大きく上がる。

インストール方法↓

（外部リンクなし）

---

### Claude Code に「Computer Use」搭載 — PC操作の自動化

- **投稿者：** @masahirochaen
- **日時：** 2026-03-30 18:38:57
- **URL：** https://x.com/masahirochaen/status/2038687441088069984

**ツイート本文（全文）：**

【速報】Claude Codeに「Computer Use」が搭載

これは半端ない。Claude Codeでブラウザだけでなく、PC操作も可能になった。理論上大体の業務は自動化できる…

・CLIからアプリ起動・UI操作・テスト検証まで自動化
・Dispatch連携でスマホから指示も可能
・macOS、Pro/Max

**外部リンク内容（全文）：** https://code.claude.com/docs/en/computer-use

Computer use is a research preview on macOS that requires a Pro or Max plan. It is not available on Team or Enterprise plans. It requires Claude Code v2.1.85 or later and an interactive session, so it is not available in non-interactive mode with the -p flag.
Computer use lets Claude open apps, control your screen, and work on your machine the way you would. From the CLI, Claude can compile a Swift app, launch it, click through every button, and screenshot the result, all in the same conversation where it wrote the code.
This page covers how computer use works in the CLI. For the Desktop app on macOS or Windows, see computer use in Desktop.

What you can do with computer use
Computer use handles tasks that require a GUI: anything you'd normally have to leave the terminal and do by hand.
Build and validate native apps: ask Claude to build a macOS menu bar app. Claude writes the Swift, compiles it, launches it, and clicks through every control to verify it works before you ever open it.
End-to-end UI testing: point Claude at a local Electron app and say "test the onboarding flow." Claude opens the app, clicks through signup, and screenshots each step. No Playwright config, no test harness.
Debug visual and layout issues: tell Claude "the modal is clipping on small windows." Claude resizes the window, reproduces the bug, screenshots it, patches the CSS, and verifies the fix. Claude sees what you see.
Drive GUI-only tools: interact with design tools, hardware control panels, the iOS Simulator, or proprietary apps that have no CLI or API.

When computer use applies
Claude has several ways to interact with an app or service. Computer use is the broadest and slowest, so Claude tries the most precise tool first:
If you have an MCP server for the service, Claude uses that.
If the task is a shell command, Claude uses Bash.
If the task is browser work and you have Claude in Chrome set up, Claude uses that.
If none of those apply, Claude uses computer use.
Screen control is reserved for things nothing else can reach: native apps, simulators, and tools without an API.

Enable computer use
Computer use is available as a built-in MCP server called computer-use. It's off by default until you enable it.

1. Open the MCP menu
In an interactive Claude Code session, run: /mcp
Find computer-use in the server list. It shows as disabled.

2. Enable the server
Select computer-use and choose Enable. The setting persists per project, so you only do this once for each project where you want computer use.

3. Grant macOS permissions
The first time Claude tries to use your computer, you'll see a prompt to grant two macOS permissions:
Accessibility: lets Claude click, type, and scroll
Screen Recording: lets Claude see what's on your screen
The prompt includes links to open the relevant System Settings pane. Grant both, then select Try again in the prompt. macOS may require you to restart Claude Code after granting Screen Recording.
After setup, ask Claude to do something that needs the GUI:
Build the app target, launch it, and click through each tab to make sure nothing crashes. Screenshot any error states you find.

Approve apps per session
Enabling the computer-use server doesn't grant Claude access to every app on your machine. The first time Claude needs a specific app in a session, a prompt appears in your terminal showing:
Which apps Claude wants to control
Any extra permissions requested, such as clipboard access
How many other apps will be hidden while Claude works
Choose Allow for this session or Deny. Approvals last for the current session. You can approve multiple apps at once when Claude requests them together.
Apps with broad reach show an extra warning in the prompt so you know what approving them grants:
Warning / Applies to:
Equivalent to shell access — Terminal, iTerm, VS Code, Warp, and other terminals and IDEs
Can read or write any file — Finder
Can change system settings — System Settings
These apps aren't blocked. The warning lets you decide whether the task warrants that level of access.
Claude's level of control also varies by app category: browsers and trading platforms are view-only, terminals and IDEs are click-only, and everything else gets full control. See app permissions in Desktop for the complete tier breakdown.

How Claude works on your screen
Understanding the flow helps you anticipate what Claude will do and how to intervene.

One session at a time
Computer use holds a machine-wide lock while active. If another Claude Code session is already using your computer, new attempts fail with a message telling you which session holds the lock. Finish or exit that session first.

Apps are hidden while Claude works
When Claude starts controlling your screen, other visible apps are hidden so Claude interacts with only the approved apps. Your terminal window stays visible and is excluded from screenshots, so you can watch the session and Claude never sees its own output.
When Claude finishes the turn, hidden apps（以下省略）

---

### コンテキスト使用率の可視化 — ccslとstatusline

- **投稿者：** @masahirochaen
- **日時：** 2026-03-30 21:49:00
- **URL：** https://x.com/masahirochaen/status/2038735267117346923

**ツイート本文（全文）：**

長時間セッションでコンテキストが肥大すると、精度が落ちるので、自分は ccslを入れて、コンテキスト使用率を常に可視化しつつ、80%超えたら強制リセットする運用にしてます。

ここからワンクリックで導入できます！

https://github.com/usedhonda/statusline

--- 引用ツイート (https://x.com/hz2on/status/2038629323238989865) ---
気になったので、今月のClaude Codeの利用量を調べてみました。

結果:
・月間21.4Mトークン消費（上位1-3%）
・API従量課金なら月¥22万相当 → 実質¥3万（86% OFF）
・年間約¥227万の節約
・450セッション / 連続30日利用中 / 最長セッション2日13時間

（外部リンクなし）

---

## カテゴリ2：Claude Code 設定・運用ベストプラクティス

---

### Claude Codeの精度を100倍にするフォルダ構造 — .claudeフォルダ完全解説

- **投稿者：** @oda_nobunaga10
- **日時：** 2026-03-29 08:23:39
- **URL：** https://x.com/oda_nobunaga10/status/2038170208142307514

**ツイート本文（全文）：**

Claude Codeを使い倒したい人は今すぐフォルダ構造を確認してくれ。ここが雑なままだと精度がガチで大幅に落ちる。「使ってるだけ」の人と「飼い慣らしてる」人の差はここにある。その差はエグいくらいデカい。知らないまま使い続けるのは時間の無駄だろ。今すぐ全員が読んで確認してくれ。

**引用ツイート内容（全文）：** https://x.com/kkk_cun/status/2038141583841980446

Claude Codeの精度を100倍にするフォルダ作り方公開

ClaudeCodeを使う前にこれを読まないと損します

ここ最近XでClaudeCodeが話題ですが、
「使ってるだけ」の人と「飼い慣らしてる」人の差がエグい
Claude Codeを触り始めて最初の1ヶ月、僕は完全に時間を溶かしていた。
毎回セッションを立ち上げるたびに

「このプロジェクトは〇〇で、テストは〇〇で、CSSは〇〇で……」って一から説明してた。

プロジェクトが変わったらまたゼロから。
先週教えたことも全部忘れてる。

当たり前だけど。
で、あるとき気づいた。
これ、僕がClaude Codeを「使ってる」んじゃなくて、
Claude Codeに「振り回されてる」だけだ。
同じことを毎回説明する。思い通りに動かない。

手戻りが発生する。「AIで効率化してるはずなのに、なんか疲れてない？」っていう矛盾。
この状態を根本から変えたのが、.claude フォルダだった。

.claude フォルダ——Claudeの「頭の中」を書き換える場所

Claude Codeのプロジェクトルートには .claude/ というフォルダを置ける。

ほとんどの人はこのフォルダの存在を知らないか、知ってても「なんかあるな」程度でスルーしてる。

僕もそうだった。

でもこのフォルダ、Claudeの脳みそそのものです。

何を知っていて、何をやっていいか、何をやったらダメか。

全部ここに定義できる。

一度書けば、毎回説明しなくてよくなる。

セッションを立ち上げた瞬間から「あ、このプロジェクトね、把握してます」という状態でClaudeが起動する。

構造はこうなってる。
```
your-project/
├── CLAUDE.md　　　　　# Claudeの「初期記憶」
├── CLAUDE.local.md　　# 個人用の追加設定（git管理外）
└── .claude/
    ├── settings.json　# 権限と安全装置
    ├── rules/　　　　 # 追加ルール（分割管理用）
    ├── skills/　　　　# 自律ワークフロー＋コマンド
    └── agents/　　　　# 専門特化した部下エージェント
```

これを一つずつ解説していく。

① CLAUDE.md —— 全てはここから始まる
CLAUDE.mdは、セッション開始時にClaudeが一番最初に読むファイルだ。
ここに書かれたことは、そのセッション中ずっとClaudeの頭に残る。
つまり「CLAUDE.mdに書いた指示は、Claudeが絶対に守るルール」になる。

たとえば「文章のトーンは丁寧語で統一して」
「出力は必ず見出し→本文→まとめの構成にして」
「URLを貼るときはリンクテキストをつけて」。

こういうことを二度と口頭で説明しなくてよくなる。

ただし注意点がある。
200行以内に収めること。

僕も最初やらかしたんだけど、張り切って400行くらい書いたことがある。結果、Claudeの指示遵守率が目に見えて落ちた。

長すぎるとコンテキストを圧迫して、大事なルールが埋もれるんだと思う。

▼ 何を書くべきか、何を書くべきでないか

【書くべきもの】
よく使うコマンドや操作手順。
プロジェクトの全体像（「ブログ運営のプロジェクトで、記事はMarkdownで管理してる」等）。
「この案件は敬語必須」「画像は必ず代替テキストをつける」等）。
文体・トーン・フォーマットの方針。

【書くべきでないもの】
他のツールや設定ファイルに書けばいいこと。
URLリンクで済むドキュメント。
長い理論的説明。

要するに「Claudeがコードを書き始める前に、絶対に知っておくべき最小限の情報」だけを書く。

それ以外は全部、後で説明する .claude/rules/ に分割する。

▼ 今すぐ使えるテンプレート（X運用の例）
```
# Project: X運用プロジェクト
 
## やること
- 毎日のポスト作成（朝・昼・夜の3本）
- リプ周り用のコメント案作成
- 週2回の長文ノート記事の執筆
 
## ルール
- 文体は「です・ます」を使わない。語りかけ口調で
- 1ポストは140文字以内。改行は2回まで
- ハッシュタグは最大3個
- 宣伝臭のある表現は禁止（「今だけ」「限定」等）
 
## ターゲット
- 副業・AI活用に興味がある30〜40代
- 月収+5万〜30万を目指している層
 
## 注意点
- 競合の名前は絶対に出さない
- 数字を使うときは根拠を添える
- 煽りすぎない。信頼感を最優先
```

② .claude/rules/ — CLAUDE.mdが太ってきたらここに分割する
CLAUDE.mdは「200行以内」が鉄則。

でもプロジェクトが育ってくると、書きたいルールがどんどん増える。
APIの規約、テストの書き方、コードスタイル、セキュリティポリシー……

全部CLAUDE.mdに突っ込んだら破綻する。
そこで .claude/rules/ ディレクトリの出番だ。
```
.claude/rules/
├── tone.md　　　　　　# 文体・トーンのルール
├── x-posting.md　　　 # X投稿のルール
├── line-writing.md　　# LINE配信文のルール
└── product-copy.md　　# 商品LPのコピーライティングルール
```

ここに置いたMarkdownファイルは、CLAUDE.mdと同じように自動で読み込まれる。
ファイルを分けることで、担当者ごとに管理できるし、チーム開発のときに「誰がどのルールを書いたか」も明確になる。
CLAUDE.mdは「全体方針」、rulesは「部門ごとの詳細マニュアル」。
この分け方が一番うまくいった。

③ .claude/skills/ —— Claudeを「自分で考えて動く部下」にする仕組み

ここが今回の記事で一番伝えたい部分だ。
かつて .claude/commands/ にあったスラッシュコマンド機能はskillsに統合されて、commandsは非推奨になっている。

新しく作るなら全部 skills に置くのが正解。

▼ commandsとskillsの違い（もう気にしなくていい）

昔のcommands：スラッシュコマンドを作るだけの単機能ファイル。

今のskills：スラッシュコマンドも作れるし、Claudeが会話の文脈を読んで自律的に起動することもできるし、サブエージェントとして独立コンテキストで動かすこともできる。

完全上位互換。

つまり「僕が呼ばなくても、Claudeが自分で判断してskillを発動する」という世界になってる。

▼ skillの作り方
```
.claude/skills/
├── code-review/
│　├── SKILL.md　　　# スキル定義（必須）
│　└── checklist.md　# 補足資料（任意）
├── security-audit/
│　├── SKILL.md
│　└── owasp-reference.md
└── x-post-writer/
　　├── SKILL.md
　　└── tone-guide.md
```

各スキルはフォルダ単位で管理する。

SKILL.mdが必須で、補足ファイルを好きなだけ添えられる。
これがcommands時代にはできなかった大きな進化。

▼ SKILL.mdの書き方
```yaml
---
name: code-review
description: PRやブランチの差分をレビューする。コードレビュー、
　マージ前チェック、品質確認などのキーワードで自動起動。
allowed-tools: Read, Grep, Glob, Bash
---

以下の観点でコード差分をレビューしてください。

1. ロジックのバグや抜け漏れ
2. セキュリティリスク（インジェクション、認証漏れ）
3. テストが書かれているか
4. パフォーマンスへの影響

ファイルごとに具体的なフィードバックを箇条書きで出してください。
問題がなければ「LGTM」とだけ返してください。
```

frontmatter（YAMLの部分）がミソだ。
name と description はClaudeがスキルを選ぶときの判断材料。description をちゃんと書いておくと、
僕が「レビューして」と言っただけで、Claudeが「あ、code-reviewスキルを使うべきだな」と自動判断してくれる。
allowed-tools はこのスキル実行中にClaudeが使えるツールを制限するもの。セキュリティ監査のスキルならRead/Grep/Globだけ許可して、
書き込み系は全部禁止する、みたいな運用ができる。

▼ 実戦で使ってるスキル例：セキュリティ監査
```yaml
---
name: security-audit
description: セキュリティ脆弱性のスキャン。デプロイ前、
　コードレビュー時、セキュリティに言及した場合に自動起動。
allowed-tools: Read, Grep, Glob
model: opus
---

以下の観点でコードベースの脆弱性を洗い出してください。

1. SQLインジェクション / XSS / CSRF
2. ハードコードされた認証情報やシークレット
3. 安全でないデフォルト設定
4. 認証・認可の抜け穴

深刻度を「Critical / High / Medium / Low」で分類し、
各項目に修正手順を添えてください。
```
model: opus でこのスキルだけOpusを使わせることもできる。

普段の作業はSonnetで回して、セキュリティみたいな
判断の重い作業だけOpusに振る。コスト最適化の鬼になれる。

④ .claude/agents/ — 専門の「部下」を雇う
agentsは、skillsとは別のレイヤーで動く独立した部下エージェントだ。
skillsが「タスク単位のワークフロー」なら、agentsは「専門職の人材」。独自のコンテキストウィンドウを持っていて、メインセッションを汚染しない。
```
.claude/agents/
├── code-reviewer.md　　 # コードレビュー専門
├── security-auditor.md　# セキュリティ専門
└── test-writer.md　　　 # テスト作成専門
```

▼ agentファイルの書き方
```yaml
---
name: security-auditor
description: コードベースのセキュリティ脆弱性を分析する専門エージェント
tools:
　- Read
　- Grep
　- Glob
model: opus
---

あなたはセキュリティ監査の専門家です。

以下のルールに従ってコードを分析してください：
- OWASP Top 10をベースに脆弱性を分類する
- 発見した問題は深刻度別にランク付けする
- 各問題に対して具体的な修正コードを提示する
- 問題がなければその旨を明記する

ファイルの書き換えは絶対にしないでください。
読み取りと分析のみを行ってください。
```

モデルは「コスパで使い分ける」
ファイルを探すだけの単純作業 → 安いHaikuで十分
「このコード、問題ある？」の判断が必要な場面 → OpusかSonnetに任せる
全部Opusで動かすのは、コピー1枚取るのに幹部を使うようなもの。コストが激変する。

▼ skillsとagentsの使い分け
【skills を使うとき】
特定のタスクを決まった手順で処理したい。テンプレートやチェックリストがある。会話の流れで自動発動させたい。
【agents を使うとき】
専門的な判断をメインセッションとは隔離してやりたい。独自のコンテキストで深く分析させたい。ツール権限を厳密にコントロールしたい。
簡単に言えば、skillsは「マニュアル」、agentsは「専門家」だ。

⑤ settings.json — Claudeに「やっていいこと」と「絶対ダメなこと」を叩き込む

.claude/settings.json は権限管理ファイルだ。ここでClaudeの行動範囲を完全にコントロールする。
```json
{
　"permissions": {
　　"allow": [
　　　"Bash(npm run *)",
　　　"Bash(git status)",
　　　"Bash(git diff *)",
　　　"Bash(npx prisma *)",
　　　"Read",
　　　"Write",
　　　"Edit"
　　],
　　"deny": [
　　　"Bash(rm -rf *)",
　　　"Bash(curl *)",
　　　"Bash(wget *)",
　　　"Read(./.env)",
　　　"Read(./.env.*)"
　　]
　}
}
```

仕組みはシンプルな3層構造。

【allow に書いたもの】→ Claudeが確認なしで即実行する。
毎回「実行していいですか？」って聞かれるあのダイアログが消える。

作業速度が爆上がりする。
【deny に書いたもの】→ Claudeが絶対に実行しない。どんなにもっともらしい理由をつけて実行しようとしても、ブロックされる。
【どちらにも書いてないもの】→ Claudeが都度「これ実行していいですか？」と確認してくる。
この3段階があるから、安全に自律走行させられる。
特に deny に .env の読み取りを入れるのは絶対にやるべきだ。

Claudeが .env の中身をうっかりコンテキストに載せて、
それがログに残ったりしたら洒落にならない。

全部繋げると、僕の開発はこうなった
.claude フォルダを整備する前と後で、僕の開発フローは完全に変わった。
【Before】
毎回プロジェクトの説明からスタート。
テストの走らせ方を教え直す。
コードスタイルを口頭で指定。
レビューも自分の目で全部見る。
「AIで効率化してるはず」なのに、なぜか21時を過ぎてもPC閉じれない。

【After】
セッション立ち上げた瞬間、Claudeはもうプロジェクトを把握してる。
コード書かせてる間に、別窓でsecurity-auditorが脆弱性をスキャンしてる。
レビューはcode-reviewerが叩き台を出す。
僕がやるのは「方向性の判断」と「最終GO」だけ。

これは大げさじゃない。

.claude フォルダの5つのパーツ（CLAUDE.md、rules、skills、agents、settings.json）を正しく設計するだけで、この状態になる。

僕の1日
　設計判断（15分）
　→ Claudeが実装を自律走行
　→ security-auditor が並列で監査
　→ code-reviewer がレビューの叩き台作成
　→ 僕が最終チェック（10分）
　→ マージ
人間がやるのは「何を作るか」の意思決定だけ。
「どう作るか」はCLAUDE.mdとskillsが規定して、「本当に大丈夫か」はagentsが検証する。

最後に「設定は後でいいや」が一番高くつく
たぶんここまで読んで「なるほどね、今度やろう」と思ってる人がほとんどだと思う。
断言するけど、「今度」は来ない。
CLAUDE.mdを書くのに30分。
skillsを2〜3個作るのに1時間。agentsの設定に30分。
settings.jsonは10分。
合計2時間ちょっとで、それ以降の全セッションが別物になる。
逆に、この2時間をケチると、今後ずっと「毎回ゼロから説明する開発」が続く。セッション100回やったら、100回分の説明コストが積み上がる。
Claude Codeは「道具」じゃない。

正しく設定すれば「部下」になる。
でも部下って、入社初日にちゃんとオリエンテーションしないと使い物にならないのと同じ。
.claude フォルダは、そのオリエンテーション資料。

---

### claude-code-best-practice — ベストプラクティスのリポジトリを参照する運用

- **投稿者：** @hatushiba_ken
- **日時：** 2026-03-29 10:19:00
- **URL：** https://x.com/hatushiba_ken/status/2038199235250962549

**ツイート本文（全文）：**

「Claude Codeのベストプラクティスが毎日TLに流れてくるけど、追うのもうめんどくさいよ」って人向けの話。

まぁ自分のことなんだけど、claude-code-best-practiceだけに従うことに決めた。

もともと海外でバズってたリポジトリで、設計や思想のベストプラクティスが日々更新されてる。
日本でバズるのも元ネタ海外のことがほとんどだし、これで十分じゃないのかなと。

ややこしいこと抜きに導入したかったら、

① このリポジトリをクローン
② 自分のプロジェクトでClaude Codeに「このリポジトリを参考に、うちのプロジェクトに合ったベストプラクティスを提案して」と依頼

これだけでOK。
今後これを参照させれば、Skillsでもエージェントでも卒なく作れるようになる。

ついでにセッション開始時に自動で git pull するフックをClaude Codeのstartup hookに設定すれば、起動するたびに最新化される。

https://github.com/shanraisshan/claude-code-best-practice

ベストプラクティスを追うことに消耗するより、具体的な仕組みの実装に時間を割いた方がいい。

**外部リンク内容（全文）：** https://github.com/shanraisshan/claude-code-best-practice

claude-code-best-practice

practice makes claude perfect

 = Agents ·  = Commands ·  = Skills

Boris Cherny on X (tweet 1 · tweet 2 · tweet 3)

🧠 CONCEPTS

| Feature | Location | Description |
|---|---|---|
| Subagents | .claude/agents/<name>.md | Autonomous actor in fresh isolated context — custom tools, permissions, model, memory, and persistent identity |
| Commands | .claude/commands/<name>.md | Knowledge injected into existing context — simple user-invoked prompt templates for workflow orchestration |
| Skills | .claude/skills/<name>/SKILL.md | Knowledge injected into existing context — configurable, preloadable, auto-discoverable, with context forking and progressive disclosure · Official Skills |
| Workflows | .claude/commands/weather-orchestrator.md | |
| Hooks | .claude/hooks/ | User-defined handlers (scripts, HTTP, prompts, agents) that run outside the agentic loop on specific events · Guide |
| MCP Servers | .claude/settings.json, .mcp.json | Model Context Protocol connections to external tools, databases, and APIs |
| Plugins | distributable packages | Bundles of skills, subagents, hooks, MCP servers, and LSP servers · Marketplaces · Create Marketplaces |
| Settings | .claude/settings.json | Hierarchical configuration system · Permissions · Model Config · Output Styles · Sandboxing · Keybindings · Fast Mode |
| Status Line | .claude/settings.json | Customizable status bar showing context usage, model, cost, and session info |
| Memory | CLAUDE.md, .claude/rules/, ~/.claude/rules/, ~/.claude/projects/<project>/memory/ | Persistent context via CLAUDE.md files and @path imports · Auto Memory · Rules |
| Checkpointing | automatic (git-based) | Automatic tracking of file edits with rewind (Esc Esc or /rewind) and targeted summarization |
| CLI Startup Flags | claude [flags] | Command-line flags, subcommands, and environment variables for launching Claude Code · Interactive Mode |
| AI Terms | | Agentic Engineering · Context Engineering · Vibe Coding |
| Best Practices | | Official best practices · Prompt Engineering · Extend Claude Code |

🔥 Hot

| Feature | Location | Description |
|---|---|---|
| Power-ups | /powerup | Interactive lessons teaching Claude Code features with animated demos (v2.1.90) |
| Ultraplan | /ultraplan | Draft plans in the cloud with browser-based review, inline comments, and flexible execution — remotely or teleported back to terminal |
| Claude Code Web | claude.ai/code | Run tasks on cloud infrastructure — long-running tasks, PR auto-fix, parallel sessions with no local setup · Scheduled Tasks |
| No Flicker Mode | CLAUDE_CODE_NO_FLICKER=1 | Flicker-free alt-screen rendering with mouse support, stable memory, and in-app scrolling — opt-in research preview |
| Computer Use | computer-use MCP server | Let Claude control your screen — open apps, click, type, and screenshot your display on macOS · Desktop |
| Auto Mode | claude --enable-auto-mode | Background safety classifier replaces manual permission prompts — Claude decides what's safe while blocking prompt injection and risky escalations · Start with claude --enable-auto-mode (or --permission-mode auto), or cycle to it with Shift+Tab during a session · Blog |
| Channels | --channels, plugin-based | Push events from Telegram, Discord, or webhooks into a running session — Claude reacts while you're away · Reference |
| Slack | @Claude in Slack | Mention @Claude in team chat with a coding task — routes to Claude Code web sessions for bug fixes, code reviews, and parallel task execution |
| Code Review | GitHub App (managed) | Multi-agent PR analysis that catches bugs, security vulnerabilities, and regressions · Blog |
| GitHub Actions | .github/workflows/ | Automate PR reviews, issue triage, and code generation in CI/CD pipelines · GitLab CI/CD |
| Chrome | --chrome, extension | Browser automation via Claude in Chrome — test web apps, debug with console, automate forms, extract data from pages |
| Scheduled Tasks | /loop, /schedule, cron tools | /loop runs prompts locally on a recurring schedule (up to 3 days) · /schedule runs prompts in the cloud on Anthropic infrastructure — works even when your machine is off · Announcement |
| Voice Dictation | /voice | Push-to-talk speech input for prompts with 20-language support and rebindable activation key |
| Simplify & Batch | /simplify, /batch | Built-in skills for code quality and bulk operations — simplify refactors for reuse and efficiency, batch runs commands across files |
| Agent Teams | built-in (env var) | Multiple agents working in parallel on the same codebase with shared task coordination |
| Remote Control | /remote-control, /rc | Continue local sessions from any device — phone, tablet, or browser · Headless Mode |
| Git Worktrees | built-in | Isolated git branches for parallel development — each agent gets its own working copy |
| Ralph Wiggum Loop | plugin | Autonomous development loop for long-running tasks — iterates until completion |

See orchestration-workflow for implementation details of Command → Agent → Skill pattern.

⚙️ DEVELOPMENT WORKFLOWS

All major workflows converge on the same architectural pattern: Research → Plan → Execute → Review → Ship

（以下省略）

---

### 定常業務を自動操縦にする — Claude Code スケジューラーの育て方

- **投稿者：** @sora19ai
- **日時：** 2026-03-30 04:07:07
- **URL：** https://x.com/sora19ai/status/2038468035192008817

**ツイート本文（全文）：**

定常業務を自動化するなら全員これ読んだ方がいい。週4.5時間が浮く

**引用ツイート内容（全文）：** https://x.com/_funzin/status/2038428560273391946

定常業務を自動操縦にする — Claude Code スケジューラーの育て方

はじめに
クラシルで開発マネージャーをしているfunzinです。
本記事では、Claude Codeのスケジューラー機能を使って定常業務を自動化し、タスクを覚えておくストレスをゼロに近づける運用フローを紹介します。EM・PM・データ分析担当者など、定常作業を抱えるすべての方を対象にしています。Desktop スケジューラーで自動化を育て、安定したらCloud スケジューラーに昇格させるアプローチが実用的だったので、その運用方法を共有します

導入の背景
毎日こなす定常作業が、以下のように存在していました。
1on1の事前準備: メンバーのSlack・Notion・GitHubの活動を収集し、1on1で話す内容や成果と改善点を整理する
チーム朝会: 朝会で出たアクションアイテムをTODOとしてSlackに投稿
議事録生成: MTG後に議事録を作成し、Notionに格納。Slackに要約を投稿
日次レポート: カレンダーからMTG一覧を取得し、日々のTODOを整理・報告
分析対応: 定期的なKPIの集計とレポート作成
これらは1つ1つの作業時間は短いものの、頭の中での管理コストが積み上がっていました。作業そのものよりも「やらなければ」と覚えておくコストが大きいです。Claude Codeのスキル機能で各作業のワークフローは定義済みでしたが、実行のトリガーは自分自身でした。スケジューラーの登場により、このトリガーも自動化できるようになりました。

Claude Code スケジューラーの概要
Claude Codeには3種類のスケジューラーが用意されています。
ref: https://code.claude.com/docs/ja/scheduled-tasks
普段メインで使っているのは Desktop と Cloud の2つです。
loopコマンドはセッション終了で消失するため、Desktop スケジューラーかCloud スケジューラーを利用するのが日常業務には合っていました。

スケジューラーが強力な理由
Claude Codeのスケジューラーが他のcronやタスクスケジューラーと異なるのは、MCPコネクタやスキルを理解した状態で定期実行ができる点です。
通常のcronジョブ（サーバーやPCで決まった時刻に処理を自動実行する仕組み）では、Slack・Notion・Google CalendarそれぞれのAPIに対して、エンジニアが個別に接続設定をコーディングする必要があります（通常は数時間〜数日の作業になります）。Claude Codeのスケジューラーでは、MCPとして接続済みのサービスをそのまま利用できます。
つまり、以下のような複数サービスを横断するワークフローを、自然言語のプロンプト1つで定期実行できます。
Google Calendarから予定を取得する
Slackの特定チャンネルからメッセージを検索する
Notionのデータベースを更新する
GitHubのPR情報を取得する
結果を整形してSlackに投稿する
個別のAPIクライアントを書く必要がなく、認証の管理も不要です。この手軽さが、自動化のハードルを大幅に下げています。

Desktop スケジューラー（Desktop scheduled tasks）
Desktop スケジューラーはClaude Desktop appで利用できます。設定した時刻に自動で起動するタスクスケジューラーのような機能です。Desktop appが起動しており、PCがスリープしていない必要があるため、完全な放置はできません。
しかし、この「手が届く距離」が利点になります。スキルの出力内容を確認し、プロンプトの調整やワークフローの修正をその場で行えます。自動化を構築する初期段階では、このフィードバックループが不可欠です。

Cloud スケジューラー（Cloud scheduled tasks）
Cloud スケジューラーは、クラウド上で実行されるためPCの起動状態に依存しません。定時になったら自動で実行され、結果が通知されます。
Cloud スケジューラーに向いているのは、以下の条件を満たすタスクです。
スキルのワークフローが安定しており、手動介入がほぼ不要
出力フォーマットが固定されている
実行結果の確認が事後で問題ない

実際に自動化した定常業務
スケジューラーとスキルの組み合わせで、以下の業務を自動化しました。

1. 1on1事前準備の自動化
毎朝9時にDesktop スケジューラーが起動し、Google Calendarからその日の1on1予定を検索します。対象メンバーが見つかると、Slack・Notion・GitHubから過去2週間の活動を収集し、活動のサマリーを整理したドキュメントを自動生成します。
```markdown
スケジュール: 毎朝 9:00（平日のみ）
実行内容:
  1. Google Calendarから当日の1on1予定を取得
  2. 対象メンバーのSlack投稿・Notionタスク・GitHub PRを収集
  3. ~/1on1-prep/{メンバー名}/{日付}_summary.md に出力
使用MCP: Google Calendar, Slack, Notion, GitHub
```
1on1の直前に慌ててメンバーの情報を収集する作業がなくなりました。

2. MTG後の議事録自動生成
定時にあるMTGは終了後にDesktop スケジューラーが起動し、MTGの内容をもとに議事録を自動生成します。議事録はNotionに保存され、関連するタスクがあればTodoリストに追加されます。NotionAIのMTGを録音を開始するだけで、あとは自動処理されます。
たとえば10:00のMTGであれば、10:30には終わっている想定でスケジューラーを設定しています。
```markdown
スケジュール: 毎朝 10:30（平日のみ）
実行内容:
  1. NotionAIで録音した議事録を取得
  2. 議事録をMarkdownに整形してSlack上に投稿
使用MCP: Slack, Notion
```

3. 日次レポートの自動生成
毎朝の始業時に、前日から未完了TODOを引き継ぎ、Google Calendarから当日のMTG一覧を取得してレポートを生成します。
```markdown
スケジュール: 毎朝 8:30（平日のみ）
実行内容:
  1. 前日のデイレポから未完了TODOを抽出
  2. Google Calendarから当日の予定を取得
  3. daily-report/YYYY/YYYYMM/YYYYMMDD.md を作成
使用MCP: Google Calendar
```

4. デイリーサマリーの自動生成
1日の終わりに、Slack・Notion・GitHub・Claude Codeの活動を自動収集し、日々の活動サマリーを追記します。
```markdown
スケジュール: 毎日 18:00（平日のみ）
実行内容:
  1. Slackの自分の投稿を時系列で取得
  2. Notionの作成・編集ページを取得
  3. GitHubのPR作成・レビューを取得
  4. カテゴリ別に整理して日次レポートに追記
使用MCP: Slack, Notion, GitHub
```
「今日何やったっけ」と振り返る時間がゼロになりました。

5. 自動化タスクのレコメンド
週次で、過去5営業日の活動データを横断分析し、手動で行っている作業の中から自動化候補を提案します。
```markdown
スケジュール: 毎週金曜 17:00
実行内容:
  1. Slack・Notion・Google Calendar・GitHubから過去5日分の活動を収集
  2. 繰り返しパターンを検出（毎日同じチャンネルへの手動投稿、定例MTG前後の準備作業等）
  3. 自動化候補をSlackのDMに送信
使用MCP: Slack, Notion, Google Calendar, GitHub
```
自分では意識していなかった繰り返し作業に気づけるようになりました。

6. 分析業務の定期実行
KPIの集計や分析など、定期的に実行する分析タスクをスケジューラーに登録しています。SQLの実行からグラフの生成、Slackへの共有まで一気通貫で処理します。
```markdown
スケジュール: 毎朝 10:00（平日のみ）
実行内容:
  1. リリース後の施策から分析したいデータを抽出
  2. 修正した内容をBIツールで可視化
  3. 分析レポートをSlackに投稿
使用MCP: Slack, Snowflake
```

Desktopで育ててCloudに昇格させる
ここまで自動化した業務を紹介しましたが、最初からCloudで動かしていたわけではありません。いきなりCloudに登録すると、プロンプトの品質が低いまま自動実行され、意味のない出力が垂れ流されます。実際に試した結果、Desktopで育ててCloudに昇格させるという段階的なアプローチが、認知負荷が低く安定して運用できると感じています。

フェーズ1: スキルの作成
まず、自動化したい業務のワークフローをスキルとして定義します。この段階では手動で実行し、出力内容を確認します。

フェーズ2: Desktop スケジューラーで試運転
スキルが安定してきたら、Desktop スケジューラーに登録します。この段階で以下の調整を行います。
プロンプトの微調整（出力フォーマット、情報の粒度）
エッジケースの対応（データが取得できない場合のフォールバック（代替処理））
実行タイミングの最適化（朝一がよいか、MTG直前がよいか）
Desktopなので実行のたびに結果を確認でき、PDCAサイクルを素早く回せます。

フェーズ3: Cloud スケジューラーに昇格
以下の条件を満たしたタスクをCloud スケジューラーに昇格させます。
手動介入なしで3回以上連続で期待通りの出力が得られた
出力フォーマットが安定している
エラー時のフォールバックが定義されている
```markdown
Desktopで試運転 → 安定したらCloudに昇格

[スキル作成] → [Desktop スケジューラー] → [Cloud スケジューラー]
  手動実行       都度確認・微調整        完全自動・放置OK
```
この流れを守ることで、不安定な自動化がCloudで実行されるリスクを防げます。

実際のスケジューラー設定例
日々試行錯誤していますが、現状は11個のスケジューラーを定常実行させています。タスクを「覚えておく」必要がなくなり、実行忘れもゼロになりました。結果として、週約4.5時間分の定常作業を自動化できています。

導入時の注意点
1. スキルの品質がそのまま自動化の品質になる
スケジューラーはスキルを定期実行するだけなので、スキル自体の品質が低いと意味のない出力が量産されます。必ずDesktopで十分にテストしてから登録してください。
2. 実行結果の通知設計
Cloud スケジューラーの実行結果を確認する手段を用意しておく必要があります。SlackのDMに結果サマリーを送信するか、特定のチャンネルに投稿するか、事前に設計しておくと運用が安定します。
3. 過剰な自動化を避ける
全ての作業を自動化する必要はありません。判断が必要な作業、コンテキストに強く依存する作業は手動のままにしておく方が品質を維持できます。自動化の対象は「手順が明確で、繰り返し頻度が高く、判断が不要な作業」に絞ることを推奨します。

まとめ
Claude Codeのスケジューラーにより、定常業務の実行トリガーを自分自身から切り離せます。Desktop スケジューラーで自動化を育て、安定したらCloud スケジューラーに昇格させる運用フローで、タスク管理の負荷を段階的に削減できます。まずは1つの定常作業をスキル化し、Desktop スケジューラーに登録するところから始めてみてください。定常業務から切り離された時間は、より判断が必要な仕事に使えます。自動化は目的ではなく、本来の仕事に集中するための手段です。

---

### 非エンジニアがClaude Codeに自己改善を任せてみた話

- **投稿者：** @ku_ni_29
- **日時：** 2026-03-30 09:02:55
- **URL：** https://x.com/ku_ni_29/status/2038542478442459517

**ツイート本文（全文）：**

非エンジニアがClaude Codeに自己改善を任せてみた話

きっかけ
Claude Codeを日常業務で使いはじめて数ヶ月。
記事を書いたり、リサーチを任せたり、自身の業務を自動化したり。便利なのは間違いないんですが、ある日ふと気になったことがありました。
「このClaudeCodeの環境って、ちゃんとメンテナンスできてるんだろうか？」
スキルは増え続けて60を超えている。設定ファイルもいつの間にか肥大化している。でも、どこに何があるか自分でも把握しきれていない。
そこで、Claude Code自身に「自分の環境を診断して、改善案を出してくれ」と頼んでみました。

何が起きたか
まず、Claude Codeに現在の設定ファイルや環境構成を全部読み込ませて、改善のための計画を立てさせました。具体的に実施したのは以下の4つです。
1：安全設定の強化。
危険なコマンドの実行を自動でブロックするルールを追加しました。
2：スキルルーティングマップの構築
例えば、「記事書いて」と言ったら適切なスキルに自動で振り分けられる仕組みを整備しました。
3：モジュラールールの整備
文体ルール、コンテキスト、コンテンツレビュー基準を独立したファイルとして整理しました。
4：設定ファイルのクリーンアップ
skillが63件も蓄積していたのを18件まで統廃合してシンプルにしました。

skillは「引き当てる仕組み」が本体だった
skillを作ること自体は難しくありません。難しいのは、適切なタイミングで適切なskillが呼び出される状態を維持することです。
skillが50個を超えると、自分でもどれを使えばいいか迷うことがあります。これはClaude Code側も同じで、ルーティングの指示がなければ汎用的な回答を返したり、毎回どのskillを使うか迷ってしまいます。
そこで、CLAUDE.mdにスキルルーティングマップを書いてもらったことで、自然言語の入力から最適なスキルへの振り分けが明確になりました。
例えば「エモい記事を書きたい」と「知見をまとめたい」では、違うスキルが起動する。これだけで最終アウトプットまでの体験が大きく変わります。

モジュラールールという整理法
Claude Codeにはrules/ディレクトリという仕組みがあります。ここにファイルを置くと、毎回の会話で自動的に読み込まれます。
今回は4つのルールファイルを作りました。
writing-tone.md：全スキル共通の文体ルール。「です・ます調」「比喩禁止」「3〜4行で改行」といった基本スタイルです。
sales-context.md：営業メールで毎回説明していた自社の情報やバリュープロポジション、自身についての説明など一度書けば二度と聞かれません。
content-review.md：公開コンテンツの品質チェック基準。記事やメールを生成した後、自動で私の発信に適した品質になっているのか、自己改善のセルフレビューが走ります。
context-management.md：長い会話でコンテキストが圧縮された後の復旧手順。書籍執筆中にページ数ルールが消えてしまう問題を防ぎます。

放っておいても劣化しない仕組みも構築
さて、ここまで設定を整えても、時間が経てばまた散らかります笑
スキルの内容は古くなるし、メモリには完了済みプロジェクトの情報が残り続けます。
そこで、週次の自己改善ループをスケジュールタスクとして設定しました。
毎週月曜の朝、Claude Codeが自分自身の環境を診断して、軽微な修正は自動で実施し、大きな変更はSlackで提案してくれます。
スキルの棚卸し、重複チェック、リンク切れの修正、メモリの確認。
これらが人間の手を介さずに回り続けます。月に一度はネットで最新のベストプラクティスも調査して、さらに自己改善を進めてくれます。

Claude Codeは「仕組みを設計するプラットフォーム」だと思う
今回やってみて強く感じたのは、Claude Codeの価値は個々のタスク実行だけじゃないという点です。
設定ファイル、ルール、skill、スケジュールタスク。これらを組み合わせることで、自分専用の業務システムや思考プロセスを設計できる。しかもそのシステム自体が、自分で自分をメンテナンスしてくれる。
非エンジニアでも、この「仕組みの設計」が特に苦労せずにできるのは、本当に偉大な発明だと感じました。必要なのは、自分がどんな仕事をしていて、何を繰り返していて、どこに難しさとその理由があるかを言語化することだけ。
非エンジニアがAIを活用する上で、Claude Codeに「自分自身を改善して」と頼めるこの体験はすごくおすすめです。ぜひ参考にしてみてください！

（外部リンクなし）

---

### Boris Chernyが紹介した「隠れた使い方15選」

- **投稿者：** @09pauai
- **日時：** 2026-03-30 08:48:01
- **URL：** https://x.com/09pauai/status/2038538728713654735

**ツイート本文（全文）：**

これはマジで有料級の情報。Claude Code開発者のBoris Chernyが「隠れた使い方15選」紹介してたんだけど、ぶっちゃけ知らない機能ばかりだった。

これ全部使いこなせたら、生産性が別次元になる。
ちょっと長いけど15個全部まとめてみた↓

（外部リンクなし・続きの投稿として存在）

---

## カテゴリ3：Claude Code ユースケース・活用事例

---

### Claude Codeのユースケース205件まとめ

- **投稿者：** @oda_nobunaga10
- **日時：** 2026-03-27 08:38:06
- **URL：** https://x.com/oda_nobunaga10/status/2037449069564731446

**ツイート本文（全文）：**

Claude Codeを毎日本気で使い込んでる俺でも、全部のユースケースが205件もあるとは正直思わなかった。コード書けない奴でも使える場面がエグいほど多い。今も知らないまま損してる人間が周りにいすぎる。AIを本当の仕事の武器にしたいなら、今すぐ目を通してくれ。絶対後悔させない。

**引用ツイート内容（全文）：** https://x.com/UC_DG54/status/2037337622935400810

Claude Codeのユースケースを205件まとめたら、見えてきたものがあった

自分が日常的にClaude Codeを使い込む中で、「他の人はどう使ってるんだろう」と思って調べ始めたのがきっかけ。
Anthropic公式ドキュメント、企業の導入事例、開発者のを中心に、重複を除いて205件。
※AIで収集させているので、中身に関してはソースを確認してご活用ください。
この記事では、その205件を俯瞰して見えてきたことを共有する。スプレッドシートは記事末尾で無料公開しているので、よかったら持って帰ってほしいです！

1. 全体像: 205件の内訳
12カテゴリに分類。
・開発: 78件
・経営: 26件
・業務効率化: 20件
・エージェント設計: 16件
・マーケティング: 10件
・コンテンツ制作: 10件
・その他（営業・人事・経理・デザイン・リサーチ・データ分析）: 45件
難易度別だと、初級が6%、中級が52%、上級が42%。「質問するだけ」の初級レベルはほとんどなく、実践的な中上級の使い方が大半を占める。

2. 見えてきたこと①: 「コーディングツール」という認識は実態とズレている
205件のうち、純粋な「コードを書く」用途は全体の3割程度。
残り7割は、経営判断の支援、営業パイプラインの自動化、スプレッドシートの自動更新、プレゼン資料の自動生成、顧客データの分析など、非エンジニア領域の活用だった。
Anthropic公式ブログでも「60%以上の企業がヘッドレスモードでCI/CDに統合」と報告されている。人間が対話的に使うだけのツールでは、もうない。

3. 見えてきたこと②: 「エージェント設計」というスキルが生まれている
205件の中で最も興味深かったのが「エージェント設計」カテゴリの16件。
・AIエージェントに役割・行動規範を定義する
・フィードバックループで出力品質を継続的に改善する
・複数エージェントを並列で動かして大規模タスクを分割処理する
・Hooksで自動フォーマット・セキュリティチェックを組み込む
これは「プロンプトエンジニアリング」の次のフェーズだと思う。
プロンプトは「1回の質問をどう投げるか」。エージェント設計は「AIをどう組織に組み込むか」。
経営者にとって、こっちのほうが本質的なスキルだと感じている。

4. 見えてきたこと③: 「使ってる」と「使いこなしてる」の間には大きな溝がある
難易度の分布を見ると、初級（プロンプトだけ）は全体の6%。
つまり、「AIに質問しているだけ」の段階では、世の中の活用事例の94%にアクセスできていない。
具体的にどういう差かというと、たとえば——
・スプレッドシートのデータを自動で読み取ってダッシュボードを構築する（中級）
・PRが作られるたびに複数エージェントが並列でコードレビューする（上級）
・毎朝、チーム全体の活動ログを集約して経営者に日報を届ける（上級）
これらは「AIに質問する」ではなく「AIに仕事を任せる」レベル。この差は、体感としてかなり大きい。

5. まとめ
205件集めて一番感じたのは、AIの使い方は「質問する」から「経営する」に移行しつつあるということです。
Claude Codeは、プログラマーだけのツールではない。経営者にとっては、もう一人の自分を作るための基盤になりつつあります。
まだ触ってない人は、スプレッドシートの中から自分の業務に一番近いものを1つ選んで、まず試してみてください！
▼ スプレッドシートはこちら（無料）
https://docs.google.com/spreadsheets/d/1WnRi_ox9m9I5ur8f1kdHIyuLgaMGepvx_lXZ_PzP-b4/edit?usp=sharing

**外部リンク内容（全文）：** https://note.com/yuto_lab_note/n/n0500cf473fef

Claude Codeのユースケース205件が話題になっていた。その中から「これは面白い」を5つ選んでみた

@UC_DG54さん（千葉勇志さん）がClaude Codeのユースケースを205件まとめたスプレッドシートが話題になっている。
開発、経営、マーケティング、人事、経理——12カテゴリにわたる実際の活用事例。 これを全部読んでいくと、「Claude Codeってコーディングツールでしょ？」という認識がひっくり返る。

205件の中から、読んでいて一番ワクワクした5つを選んだ。 「こんなことできるのか」「これ自分でもやってみたい」と思ったものだけを厳選してみたので紹介する。

AIで「本」を作る工場ライン（No.96 / コンテンツ制作）

ブログ記事をAIで書くのは、もう珍しくない。

じゃあ、数万字の書籍は？

No.96の「Book Factory」は、Claude Codeの中に本の制作ラインを作る事例だ。

仕組みはこうなっている。

リサーチエージェントがローカルの資料フォルダを読み込んで素材を集める

構成エージェントが章立てを設計する

執筆エージェントが1章ずつ書く（前の章を参照しながら）

校正エージェントが全体を通して文体統一とファクトチェックをかける

これがClaude Codeのファイルシステムアクセスを活かして、1つのプロジェクトとして回る。

面白いのは、CLAUDE.mdにワークフローを定義しておけば、毎回同じ品質で回せるところ。 電子書籍を量産する出版社みたいなことが、1人でできる。

フリーランスのエンジニアが技術書を書いてKDPに出す、みたいな流れは普通にありだと思う。

やってみたい度: かなり高い。 ブログ記事は1本2,000〜5,000字で書いてるけど、3万字クラスの電子書籍をClaude Codeで作ってKDPに出す、みたいな流れは普通にありだと思う。

AIに「感情」を記録させる（No.202 / エージェント設計）

これは発想がすごかった。

emotion-log.md というファイルをプロジェクトに置いて、Claude Codeに自分の状態を記録させる。

記録する項目はこういうもの。

confidence: この判断に自信があるか

frustration: 行き詰まっているか

curiosity: 面白いと感じているか

energy: 処理負荷が高いか低いか

AIが「感情を持つ」わけじゃない。 でもセルフモニタリングの仕組みとして、自分の状態を言語化させると、後からデバッグできる。

「このタスクでconfidenceが急落してる」→「ここで判断ミスが起きたんだな」

長時間セッションの後半で挙動がおかしくなる問題、Claude Codeを使い込んでる人なら心当たりがあるはず。 emotion-logがあれば「どこから迷走が始まったか」が見える。

人間の日記に近い。
AIにも日記を書かせると、デバッグ効率が上がるというのが面白かった。

やってみたい度: 中の上。 まずは自分のCLAUDE.mdに「セッション中の判断confidence を記録せよ」と書くところから試せそう。

デザインとコードの壁が消える（No.36 / 開発）

デザイナーが作ったFigmaのデータを、エンジニアがコードに落とす。 この「翻訳作業」に毎回時間がかかる。

No.36は、Figma → Claude Code → Figma の双方向ワークフローだ。

Figma MCPを使って、デザインデータをClaude Codeが直接読み取る。 コンポーネント名、余白、色、フォントサイズをそのまま受け取ってコードに変換する。

逆に、コードの変更をFigma側に反映させることもできる。

これが面白いのは、「デザイナーとエンジニアの間の議論」が減る点。 「ここの余白、デザインと違いませんか？」というやりとりが、そもそも発生しなくなる。

1人でプロダクトを作ってるフリーランスにとっては、デザインとコードを行ったり来たりする時間が大幅に減る。 チームでやってる場合は、レビューのコストが激減する。

人生設計をシミュレーションする（No.107 / その他）

完全にコーディングの外の話。

No.107は、Claude Codeでライフプランシミュレーターを構築する事例。

収入の推移、支出の変化、ライフイベント（結婚、住宅購入、退職）をパラメータとして入力する。 Claude Codeがそれをもとにシミュレーションを組んで、10年後・20年後・30年後の資産推移をグラフ化する。

「もし35歳で家を買ったら」「もし副業収入が月10万増えたら」 こういう条件分岐を入れて、複数のシナリオを比較できる。

エンジニアなら「スプレッドシートでやれば？」と思うかもしれない。 でもClaude Codeの強みは、自然言語でパラメータを変更できる点。

「子どもが2人に増えた場合のシナリオを追加して」と言えば、計算ロジックの修正からグラフの更新まで全部やってくれる。 スプレッドシートの数式をいじる必要がない。

26歳の自分がこれで30年先を見てみたら、「ああ、フリーランスの国民年金だけだとこうなるのか」と現実を突きつけられそう。 でもそれを知っておくことに価値があると思った。

PRを9人のAIが同時レビューする（No.128 / 開発）

最後はエンジニア向けだけど、スケールがすごい。

1つのPull Requestを、9つのAIエージェントが並列でレビューする。

各エージェントに役割が違う。

セキュリティ担当

パフォーマンス担当

コードスタイル担当

テストカバレッジ担当

ドキュメント整合性担当

……

これをGit Worktreeで分離された環境で同時に走らせて、結果を集約する。

人間のレビュアーが9人いる会社はそうそうない。 でもAIなら、観点別に何人でも増やせる。

自分は1人でコードを書いてレビューも自分でやるスタイルだけど、「セキュリティだけは毎回チェックしてほしい」みたいな使い方は現実的だと思う。

9人全員をいきなり導入する必要はない。 まず1-2人のAIレビュアーから始めて、徐々に増やしていく。

まとめ

205件を読んで強く感じたのは、Claude Codeの守備範囲が想像以上に広いということ。

振り返ってみると、今回の5つには共通点がある。

書籍制作パイプライン → 「量」のスケールが違う

感情ログ → AIの「内省」という発想

Figma双方向 → 「一方通行」を「双方向」にする

ライフプランシミュレーター → 開発ツールを「人生のツール」にする

9エージェント並列 → 「1つのAI」を「9つの専門家」にする

どれも、Claude Codeの基本機能（ファイル読み書き、CLI実行、コンテキスト保持）は同じ。 でも使い方の発想が全然違う。

自分が毎日やってる使い方って、どうしても自分の仕事の延長線上になる。 205件のリストの価値は、「自分の外側」の使い方を見せてくれるところにあると思う。

元ポスト（@UC_DG54さん）はこちら。
事例をまとめたスプレッドシートも公開されてる。

https://x.com/UC_DG54/status/1904051746508898706

205件、まだ読んでない人はぜひ一度眺めてみてほしい。 自分の使い方の外側に、けっこう面白い世界が広がってる。

https://t.co/gQGRdfgHWB

---

### Anthropic公式「Claudeのユースケース74選」— プロンプト付き手順付きで全部載ってる

- **投稿者：** @SuguruKun_ai
- **日時：** 2026-03-29 08:32:47
- **URL：** https://x.com/SuguruKun_ai/status/2038172507807871210

**ツイート本文（全文）：**

Anthropicが公開してる
「Claudeのユースケース74選」が手厚すぎて神だった。

Claude / Claude Cowork/ Claude Codeのユースケースが
プロンプト付き・手順付き・使う機能の説明付きで全部載ってます。

・Personal（個人向け）15件
・Professional（プロフェッショナル向け）15件
・Nonprofits（非営利団体向け）12件
・Education（教育向け）11件
・Finance / Research / Sales / Legal / Life Sciences / Marketing / HR

何がすごいかというと
「Claudeで何ができるか」じゃなくて
「どうやるか」まで各ページに書いてある

例えば、

・コードを一切書かずにポートフォリオサイトを作る
→ Artifactsを使って、指示の出し方まで載ってる

・散らかった180個のファイルを5つのフォルダに自動整理
→ Claude Coworkにフォルダを読ませて分類させる手順

・ブランドアセット（ロゴ/配色/フォント）を一括生成
→ Projectsにブランド情報を保存→使い回す流れ

・投資メモのドラフトを自動作成
→ 財務データの読み方+プロンプト例

Xの記事ブクマももちろんいいけど、
公式サイトもかなり良いのでぜひ

**外部リンク内容（全文）：** https://claude.com/resources/use-cases

Meet Claude
Platform
Solutions
Pricing
Resources
Login
Contact sales
Try Claude

Use cases
Explore here

Get inspired by what you can do with Claude

Browse practical examples across research, writing, coding, analysis, and everyday tasks, whether you're working solo or with a team.

Filter
Category
Features
Product
Search

See your theory of change in chat with Claude
Describe your program and Claude draws the causal chain inline, inputs through impact, with every arrow clickable to show the assumption behind it. For when you know what you do but have never drawn why it works.
Anthropic / Nonprofits

Plan your syllabus
Attach your syllabus and Claude shows which weeks are locked by real prerequisites and which you're free to rearrange — right in chat as you work through the order.
Anthropic / Education

Work through grant options in chat
Claude plots every funder in one view — odds, award, deadline, effort — and you filter, test scenarios, ask for a prioritization, narrow down together. For decisions where no single sort order shows the full picture.
Anthropic / Education

Apply a formula as you learn it
Claude builds a blank scatter right in the conversation — you place the points, drag them, watch what happens to the fit. For when you can do the calculation but don't yet have a feel for it.
Anthropic / Education

Bring your whiteboard lesson to life
Work through how to teach a concept with Claude sketching alongside. The visual streams in as part of the back-and-forth — a thinking tool for your prep first, and a teaching tool if you take it further.
Anthropic / Education

Visualize the mechanism behind an explanation mid-chat
Claude builds an interactive visual inline as you talk through the problem — shaped to the specific question you're asking, with controls you manipulate and buttons that drill deeper. Useful when a concept has moving parts text can't show.
Anthropic / Education

Update your financial model after earnings
Cowork pulls the release and transcript from S&P and checks them against your financial model. You take the flags into Claude for Excel to edit the cells, then open the deck in Claude for PowerPoint to build the page.
Anthropic / Finance

See what your campaign goal actually requires
Type a campaign goal and Claude draws the gift pyramid inline, tiered from the lead gift down, with each tier showing how many gifts you need and how many qualified prospects that realistically takes. Drag the goal and the whole shape rebuilds. For when you're wondering whether a campaign is feasible before you say yes to it.
Anthropic / Nonprofits

See budget futures side by side, in chat with Claude
Type your budget split and the thing that might change, and Claude draws three scenarios next to each other with a toggle between dollars and percentages. Click any scenario for a one-line read on where the real pressure lands.
Anthropic / Nonprofits

See why donor retention beats acquisition, in chat with Claude
Claude builds a five-year donor projection with sliders for retention and acquisition. Drag either one and the curve redraws, and it becomes clear fairly quickly why a modest retention bump does more than doubling the acquisition spend.
Anthropic / Nonprofits

Map your lit review mid-conversation to surface the underlying debate
Claude reads your stack of papers and draws the argument structure inline — clusters by claim, tension lines where camps disagree, blind spots per group. A reading of the debate you test against your own, as you work through the set.
Anthropic / Education

Chart your data in conversation with Claude before you commit to a reading
Upload a CSV and Claude builds the correlation grid inline, flagging the patterns worth a second look. The flags are a starting point — you click into what's interesting and the conversation goes from there.
Anthropic / Education

Create brand assets
Generate professional business cards, flyers, and marketing materials that match your exact branding guidelines—ready to print or edit.
Anthropic / Professional

Create a custom webpage
Build a portfolio site to showcase your work and learn how to deploy it live without writing a line of code.
Anthropic / Personal

Contract redlining and negotiation
Analyze agreements to spot terms affecting your work, with suggested redlines and negotiation points.
Anthropic / Legal

（以下省略）

---

## カテゴリ4：Claude Cowork

---

### 【神アプデ】Claude Coworkにプロジェクト機能追加

- **投稿者：** @daifukujinji
- **日時：** 2026-03-30 13:05:49
- **URL：** https://x.com/daifukujinji/status/2038603603070599228

**ツイート本文（全文）：**

（本文なし・引用ツイートのみ）

**引用ツイート内容（全文）：** https://x.com/Hoshino_AISales/status/2038586757525196934

【神アプデ】Claude Coworkにプロジェクト機能追加

3/20。Claude Coworkに「プロジェクト機能」がついに追加されました。
これ、正直に言うと2026年で一番嬉しいアップデートです。

Coworkは「ただのチャットAI」ではなく、仕事を委任できるAIエージェントです。非エンジニアの僕の中でCoworkは最強のAIエージェント。 
ファイルを読んで、Excelを作って、パワポを生成して、メールまで送ってくれる。
でも、たった1つだけ致命的な弱点があったんです。
「毎回、ゼロからやり直し」。
この問題が、2026年3月20日に完全に解消されました。
しかも、プロジェクト機能の中身がめちゃくちゃ豊富です。 カスタム指示、メモリ、ローカルフォルダ指定、タスクの定期実行。
これだけ揃うと、非エンジニアがClaude Codeを無理して使う理由がなくなります。 正直、Claude.ai（ブラウザ版）を使う理由すら薄くなってきました。
この記事では、Coworkのプロジェクト機能で何ができるのか、どう設定するのか、Claude.aiのプロジェクトと何が違うのかを、実際に使っている僕の視点から徹底解説します。

第1章：Coworkの「唯一の弱点」がついに消えた — プロジェクト機能とは何か
Coworkを使ったことがある方なら、この不満を感じたことがあるはずです。
「さっき説明したこと、もう忘れてるの？」
Coworkはめちゃくちゃ優秀です。 指示を出せば、ファイルを読んで、計画を立てて、実際に手を動かして成果物を納品してくれます。
でも、セッションが終わると全部リセットされていました。
次にCoworkを開いたとき、また同じ説明をしなければいけない。 「前回の続きで」が通じない。

スタートアップベンチャーで働いていた時代、新しく入ったメンバーに毎朝同じ説明をしていた時期がありました。 「昨日やったこと覚えてる？」「あ、すみません、もう一回教えてください」。
あの感覚です。

Coworkのプロジェクト機能は、この問題を根本から解決しました。
2026年3月20日、Anthropic公式がX（旧Twitter）で発表しました。

プロジェクト機能とは、関連するタスク・ファイル・カスタム指示・メモリを1つのワークスペースにまとめて管理できる仕組みです。
一言でいうと、Coworkが「使い捨ての新人」から「自分のことを覚えている相棒」に変わりました。

Claude.ai（ブラウザ版）にはもともとプロジェクト機能がありました。 ファイルやカスタム指示を事前に設定しておける、ChatGPTのGPTs（カスタムGPT）に近い機能です。
でも、Claude.aiのプロジェクトは「チャット」の中でしか使えませんでした。 つまり、アドバイスはくれるけど、実際にファイルを作ったりフォルダを整理したりはできない。
今回のアップデートで、このプロジェクト機能がCoworkに統合されたんです。
カスタム指示を設定して、ファイルを紐づけて、メモリで文脈を保持して、さらに定期タスクまで自動実行できる。
これは「チャットのプロジェクト」とは次元が違います。

プロンプト例を1つ紹介します。 プロジェクトを初めて作ったら、まずこれを投げてください。
```
このプロジェクト内のすべてのファイルを読み込んで、
以下を整理して教えてください。

1. このワークスペースに何が入っているか
2. 僕がこのプロジェクトを何の目的で使おうとしているか
3. 設定されているカスタム指示の内容
4. 不明点があればAskUserQuestionで確認して
```
コピペしてそのまま使えます。
このプロンプトの意図は、Coworkに「初日のオリエンテーション」をさせることです。 プロジェクトの全体像を把握させることで、以降のタスクの精度が格段に上がります。
僕はこれを「Day 1プロンプト」と呼んでいます。 新しいメンバーが入ったら、まず「うちの仕事の全体像を理解して」と言いますよね。 AIも同じです。

第2章：Coworkプロジェクト機能の中核 — カスタム指示・メモリ・フォルダ・定期タスク
プロジェクト機能には4つの中核があります。 1つずつ解説します。

中核1：カスタム指示（Instructions）
プロジェクトごとに「このプロジェクトではこういうルールで動いて」という指示を設定できます。
たとえば、経理業務のプロジェクトなら「出力は必ずExcel形式」「金額は税込と税抜を両方記載」。 マーケティング分析なら「競合はA社・B社・C社の3社を常に比較対象にする」。
これ、毎回チャットで説明していた内容を一度だけ設定すれば済むんです。
Claude.aiのプロジェクト指示とほぼ同じ概念ですが、決定的な違いがあります。 Coworkのカスタム指示は「作業」に反映されるということです。
チャットのプロジェクト指示は、回答のトーンや内容に影響します。 Coworkのカスタム指示は、ファイルの作り方、保存場所、フォーマットまで全部コントロールできます。

プロンプト例です。
```
【カスタム指示の設定例】
このプロジェクトでは以下のルールに従ってください。

- 出力ファイルはすべて「output」フォルダに保存する
- ファイル名は「YYYYMMDD_タスク名」の形式にする
- レポートはMarkdown形式で作成する
- 計画を先に見せて、承認してから実行すること
- 不明点があれば必ず質問すること
```
コピペしてそのまま使えます。

中核2：プロジェクト単位のメモリ
これが一番の目玉です。
プロジェクト内で実行したタスクの文脈を、Coworkが記憶してくれます。
「先週作ったレポートの続きをやって」が通じるようになりました。
しかも、メモリはプロジェクト単位でスコープ（範囲）が区切られています。 「経理プロジェクト」で覚えたことが「マーケティングプロジェクト」に漏れることはありません。
これ、地味にすごく大事です。
たとえば、経理の数字に関する指示が、マーケティングの分析に混ざったら事故になりますよね。 プロジェクトごとにメモリが独立しているから、そういうリスクがゼロになります。

中核3：ローカルフォルダの指定
プロジェクトに紐づけるフォルダを指定できます。
ここがCoworkの真骨頂です。 パソコンの中にある実際のフォルダを、そのままAIの作業場所として使えます。
しかも、プロジェクト機能では「コンテキスト用のフォルダ」と「出力用のフォルダ」を分けることができます。
たとえば、参考資料のフォルダは読み取り用として指定して、成果物は別のフォルダに保存させる。 これによって、元のファイルが勝手に書き換えられるリスクを減らせます。

中核4：スケジュールタスク（定期実行）
プロジェクトに紐づけた定期タスクを設定できます。
「毎週月曜日の朝9時に、先週の売上データを集計してレポートを作って」
こんな指示を一度設定するだけで、毎週自動で実行されます。
Cowork単体でもスケジュール機能はありましたが、プロジェクト機能と組み合わさることで、定期タスクがプロジェクトのカスタム指示とメモリを活用した状態で実行されるようになりました。
つまり、「前回のレポートとの差分」を踏まえた定期レポートが自動で作れるということです。

プロンプト例です。
```
/schedule

以下のタスクを毎週月曜日の9:00に実行してください。

1. 「sales_data」フォルダ内の最新CSVファイルを読み込む
2. 前週比で売上が10%以上変動した商品をリストアップ
3. 変動理由の仮説を3つ挙げる
4. Excelレポートにまとめて「output」フォルダに保存
5. レポートのファイル名は「weekly_sales_YYYYMMDD.xlsx」
```
コピペしてそのまま使えます。
注意点として、スケジュールタスクはパソコンが起動中かつClaude Desktopアプリが開いている間だけ実行されます。 パソコンがスリープしていると動きません。 ただし、スリープから復帰したときに、未実行のタスクを自動で実行してくれる仕組みはあります。

第3章：プロジェクトの作り方は3パターン — ゼロから・インポート・既存フォルダから
プロジェクトの作成方法は3つあります。 それぞれ向いているケースが違うので、自分に合った方法を選んでください。

パターン1：ゼロから新規作成
Claude Desktopアプリを開いて、左サイドバーの「プロジェクト」から「新規+」をクリックします。 「Start from scratch」を選択して、プロジェクト名を入力します。
新しいフォルダをパソコン上に作成して、カスタム指示を設定して、必要なファイルを追加します。
これが一番シンプルです。 新しいワークフローをゼロから構築したいときに使います。

パターン2：Claude.aiのチャットプロジェクトからインポート
これが既存ユーザーには一番嬉しいパターンです。
Claude.ai（ブラウザ版）で作り込んだプロジェクトを、そのままCoworkに取り込めます。
プロジェクト作成画面で「Import from a Claude project」を選択すると、Claude.aiのプロジェクト一覧が表示されます。 インポートしたいプロジェクトを選ぶと、ファイルとカスタム指示がCowork側に転送されます。
僕はClaude.aiのプロジェクトに2万文字のカスタムプロンプトとナレッジファイルを設定して記事を書いていました。 この資産をCoworkにそのまま持ち込めるのは、正直かなり大きいです。
ただし注意点があります。 インポートは「一方通行」です。 Cowork側で変更しても、Claude.aiのプロジェクトには反映されません。 逆も同じです。

パターン3：既存のローカルフォルダから作成
パソコン上にすでにあるフォルダを、そのままプロジェクトとして使う方法です。
「Use an existing folder」を選択して、フォルダを指定するだけです。
たとえば、普段使っている「業務資料」フォルダをそのまま指定すれば、わざわざファイルをコピーする手間がありません。
ただし、セキュリティの観点から、機密ファイルが含まれるフォルダをそのまま指定するのは避けてください。 専用の作業フォルダを作って、必要なファイルだけをコピーする方法がおすすめです。

プロジェクト作成直後に投げるプロンプトとして使えます。
```
このプロジェクトのフォルダ内のファイルをすべて確認して、
以下の形式で一覧を作成してください。

| ファイル名 | 種類 | サイズ | 最終更新日 | 内容の要約（1行） |

一覧を作成したら、このプロジェクトで最初に取り組むべきタスクを
3つ提案してください。
```
コピペしてそのまま使えます。

この3パターンの使い分けを整理します。
新しい業務フローを作りたい → パターン1（ゼロから）
Claude.aiで育てたプロジェクトがある → パターン2（インポート）
すでに作業フォルダがパソコンにある → パターン3（既存フォルダ）

第4章：これでClaude.aiを使う理由がなくなってきた — チャットプロジェクト vs Coworkプロジェクト
ここからが、この記事で一番伝えたいことです。
Claude.aiのプロジェクト機能とCoworkのプロジェクト機能、何が違うのか。

結論から言います。
Claude.aiのプロジェクト ＝ 「賢い相談相手」にルールを覚えさせる機能
Coworkのプロジェクト ＝ 「優秀な同僚」にルールを覚えさせて、仕事まで任せる機能

この違いは決定的です。
Claude.aiのプロジェクトでは、カスタム指示を設定して、ナレッジファイルを読み込ませて、そのプロジェクト内のチャットで一貫した回答を得られます。
でも、最終的に「作業」をするのは自分です。 Claudeが書いてくれた文章をコピペして、自分でファイルに保存して、自分でフォルダを整理する。
Coworkのプロジェクトは違います。 カスタム指示に従って、メモリで文脈を保持しながら、ローカルフォルダ内のファイルを直接操作して、成果物を保存してくれます。
しかも定期タスクまで自動で回してくれる。
「相談相手」と「同僚」の違いです。

同じタスクをClaude.aiとCoworkで比較してみます。
タスク：先月の売上データを集計して、月次レポートをExcelで作成する

Claude.ai（チャットプロジェクト）の場合：
1. CSVファイルをチャットにアップロードする
2. 「このデータを集計してExcelで出力して」と指示する
3. Claudeがコード実行でExcelを生成してくれる
4. ダウンロードボタンを押してファイルを保存する
5. 自分でフォルダに整理する

Cowork（プロジェクト機能）の場合：
1. 「先月の売上レポートを作って」と指示する
2. 放置する
3. outputフォルダにExcelが保存されている

手順が3分の1になっています。
しかも、Coworkのプロジェクト機能ではメモリがあるので、「前月と同じフォーマットで」と言えば通じます。 Claude.aiでは毎回「こういうフォーマットで」と指定し直す必要があります。

ここで、非エンジニアにとって重要なポイントを伝えます。
Claude Codeを無理して使う必要はもうありません。

Claude Codeはターミナル（黒い画面）で操作するエンジニア向けのツールです。 できることは最強ですが、操作にはプログラミングの知識が必要です。
でも、Coworkのプロジェクト機能があれば、Claude Codeでやっていたことの多くがGUIで（画面をクリックする操作で）実現できます。
ファイル操作、Excel作成、定期レポート、メール連携、カレンダー連携。 非エンジニアの業務で必要なことは、ほぼCoworkで完結します。

判断基準はシンプルです。
「プログラミングをするか？」
→ Yes → Claude Code
→ No → Coworkのプロジェクト機能で十分
これだけです。

プロンプト例を1つ紹介します。 Coworkのプロジェクト機能で「専属アシスタント」を作るためのカスタム指示テンプレートです。
```
【プロジェクト名：日次業務アシスタント】
役割：
あなたは僕の日次業務をサポートするアシスタントです。

ルール：
- タスクを実行する前に必ず計画を提示して承認を待つ
- ファイルは「output」フォルダに保存する
- ファイル名は「YYYYMMDD_内容」の形式
- レポートはExcelで作成する
- 不明点があれば必ず質問する
- 前回のタスク結果を踏まえて作業する

対応業務：
1. メールの下書き作成
2. 売上データの集計とレポート生成
3. 会議資料のドラフト作成
4. 競合情報のリサーチとまとめ
```
コピペしてそのまま使えます。

第5章：知っておくべき注意点と現時点の制限
プロジェクト機能はめちゃくちゃ便利ですが、現時点での制限もあります。

制限1：クラウド同期がない
プロジェクトのデータはローカル（自分のパソコン）に保存されます。 クラウドに同期されません。
つまり、会社のパソコンと自宅のパソコンで同じプロジェクトを使うことはできません。
ただし、スマホからDispatch（ディスパッチ）機能を使ってタスクを送ることはできます。 スマホから指示を出して、パソコン上のCoworkが実行してくれる仕組みです。 ファイルとメモリ自体はデスクトップに残ります。

制限2：チーム共有ができない
Team・Enterpriseプランでも、Coworkのプロジェクトを他のメンバーと共有する機能は未対応です。
チームで共有したい場合は、今のところClaude.ai（ブラウザ版）のプロジェクトを使う必要があります。
Anthropicは「チーム共有機能は将来対応予定」と公式に記載していますが、具体的な時期は未定です。

制限3：Claude Codeでは使えない
現時点では、プロジェクト機能はCowork専用です。 Claude Codeでの対応は将来予定とされていますが、こちらも時期は未定です。

制限4：使用量の消費が大きい
Coworkのプロジェクト1セッションは、通常のチャット20回分以上の使用量を消費します。
Proプラン（月額$20）だと、すぐに使用制限に達する可能性があります。 Coworkをがっつり使うなら、Max 5x（月額$100）以上がおすすめです。
僕はMax 20x（月額$200）を使っていますが、プロジェクト機能で定期タスクを複数設定していると、それでも使用量は気になるレベルです。
スケジュールタスクも使用量を消費するので、頻度設定は実際のニーズに合わせて調整してください。

制限5：パソコンを起動しておく必要がある
CoworkはClaude Desktopアプリ上で動きます。 アプリを閉じるとセッションが終了します。
スケジュールタスクも、パソコンが起動中かつアプリが開いている間だけ実行されます。
「完全に放置で24時間動かしたい」という使い方は、現時点ではできません。
ただし、スリープから復帰したときに未実行のタスクを自動実行する仕組みはあるので、朝パソコンを開けば溜まっていたタスクが順次処理されます。

プロジェクトの安全な運用のためのチェックリストを、Coworkに作らせるプロンプトです。
```
このプロジェクトの安全チェックリストを作成してください。

確認項目：
- 作業フォルダに機密情報が含まれていないか
- バックアップフォルダが存在するか
- カスタム指示に「計画を先に見せて承認後に実行」が含まれているか
- 出所不明のファイルが含まれていないか
- スケジュールタスクの頻度が適切か

チェックリストをMarkdownで作成して、
このプロジェクトのフォルダに保存してください。
```

おわりに：「使い捨ての新人」が「自分を覚えている相棒」になった日
Coworkのプロジェクト機能は、AIとの付き合い方を根本から変えるアップデートです。
これまでのCoworkは「毎朝リセットされる新人」でした。 毎回同じ説明をして、毎回同じルールを伝えて、毎回同じファイルを指定する。
プロジェクト機能が入ったCoworkは「自分のことを覚えている相棒」です。 ルールを覚えている。前回の仕事を覚えている。定期的な仕事は自動で回してくれる。
しかも、Claude.aiのプロジェクトからインポートできるので、これまで育ててきたナレッジ資産がそのまま使えます。
非エンジニアの方は、もうClaude Codeを無理して使わなくて大丈夫です。 Coworkのプロジェクト機能で、十分すぎるほどの自動化が実現できます。
まずは1つ、プロジェクトを作ってみてください。 「Day 1プロンプト」を投げて、Coworkにワークスペースを理解させるところから始めるのがおすすめです。

---

## カテゴリ5：AIエージェント・開発ツール

---

### dev-browser — AIエージェントに本物のPlaywrightブラウザを持たせる

- **投稿者：** @Suryanshti777
- **日時：** 2026-03-30 10:17:44
- **URL：** https://x.com/Suryanshti777/status/2038561304605315175

**ツイート本文（全文）：**

速報…誰かがClaudeに本物のブラウザを与えました。

スクリーンショットではありません。
脆いセレクターではありません。
遅いMCPループではありません。

本物のPlaywrightコード — サンドボックス内で。

それはdev-browserと呼ばれ、AIエージェントが開発者のようにChromeを制御できるようにします。

これがなぜ違うのか：

新しい「エージェント構文」を発明する代わりに、
dev-browserはAIが実際のブラウザコードを書くことを可能にします。

goto
click
fill
evaluate
scrape
screenshot

すべて。

そしてそれはQuickJSサンドボックスで実行される — だからエージェントはシステムに触れずに完全なブラウザ制御を得ます。

つまり：

• 本物のブラウザ自動化
• ホストアクセスリスクゼロ
• 永続的なタブ
• マルチスクリプトワークフロー
• 既存のChromeへの接続
• 完全なPlaywright API

重要なアイデアはシンプルです：

AIがブラウザを使う最も速い方法
は、それ自身がブラウザコードを書くことを許すことです。

だからエージェントは文字通り：

Xを開く
スクロール
ツイートを抽出
JSONを返す

すべて1回の実行で。

プラグインなし。
拡張機能なし。
オーケストレーションレイヤーなし。
MCPの複雑さなし。

ただ：

install → Claudeに「dev-browserを使って」と伝える → 完了。

さらに良いことに、スクリプトは永続的なページに対して実行されます。

だからエージェントは：

一度ログイン
一度ナビゲート
コンテキストを再利用
ワークフローを継続

今、あなたは次のようなものを手に入れます：

• 自律的な研究エージェント
• AIによるウェブサイトQAテスト
• MCPオーバーヘッドなしのスクレイピング
• マルチステップブラウザワークフロー
• 実際にウェブアプリを使うAI
• 本物のダッシュボードを操作するClaude

そしてセキュリティモデルはクリーンです：

Playwrightのパワー
QuickJSサンドボックス
ファイルシステムアクセスなし
ホスト実行なし

だからエージェントは強力 — しかし封じ込められています。

ベンチマークも驚異的です：

Dev Browser
3m 53s
$0.88
29 turns
100% success

典型的なセットアップより速くて安いです：

• Playwright MCP
• Chrome拡張機能
• browser skills

私たちは移行しています：

ウェブを見るAI
→ ウェブを操作するAI

それは大きな変化です。

なぜなら、一度AIがブラウザを信頼性を持って制御できるようになれば、
UIを持つどんなソフトウェアでも使えます。

API不要。
統合不要。

ただページを開く — そして作業する。

AI同僚に手が付きました。

（外部リンクなし）
