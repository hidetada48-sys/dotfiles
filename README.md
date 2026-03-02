# dotfiles - Claude Code 環境セットアップ

別PCでClaude Codeの環境を再現するための手順書。

---

## このリポジトリに含まれるもの

| ファイル | 役割 |
|---------|------|
| `CLAUDE.md` | Claudeの行動ルール（日本語回答・シンプル説明など） |
| `claude/settings.json` | Claude Code本体の設定（モデル・プラグイン・フック） |
| `claude/scripts/gdrive-download.sh` | セッション開始時にGoogle DriveからMEMORY.mdを取得 |
| `claude/scripts/gdrive-upload.sh` | セッション終了時にMEMORY.mdをGoogle Driveに保存 |

---

## セットアップ手順

### 1. このリポジトリをclone

```bash
git clone https://github.com/hidetada48-sys/dotfiles.git ~/dotfiles
```

### 2. ファイルを所定の場所に配置

```bash
# Claude Code設定ディレクトリを作成
mkdir -p ~/.claude/scripts

# CLAUDE.md（Claudeのルール）
cp ~/dotfiles/CLAUDE.md ~/.claude/CLAUDE.md

# settings.json（Claude Code設定）
cp ~/dotfiles/claude/settings.json ~/.claude/settings.json

# 同期スクリプト
cp ~/dotfiles/claude/scripts/gdrive-download.sh ~/.claude/scripts/
cp ~/dotfiles/claude/scripts/gdrive-upload.sh ~/.claude/scripts/

# スクリプトに実行権限を付与
chmod +x ~/.claude/scripts/gdrive-download.sh
chmod +x ~/.claude/scripts/gdrive-upload.sh
```

### 3. rcloneをインストール（Google Drive同期用）

```bash
curl https://rclone.org/install.sh | sudo bash
```

インストール後、Google Driveを設定：

```bash
rclone config
```

設定の流れ：
1. `n` → 新規リモート作成
2. 名前: `gdrive`
3. ストレージ: `drive`（Google Drive）
4. Client ID / Secret: そのままEnter（空欄でOK）
5. スコープ: `1`（フルアクセス）
6. ブラウザ認証を完了する

確認：
```bash
rclone lsd gdrive:
```

### 4. GitHubトークンを設定

```bash
echo 'export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

※ トークンはGitHub → Settings → Developer settings → Personal access tokens で発行。

### 5. GitHub MCPサーバーを設定

Claude Codeを起動した状態で以下を実行（またはClaude Codeに依頼）：

```bash
claude mcp add github \
  -e GITHUB_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN \
  -- npx -y @modelcontextprotocol/server-github
```

### 6. Claude Codeを起動

```bash
claude
```

初回起動時にclaude-memプラグインが自動インストールされる。  
Google DriveからMEMORY.md（記憶ファイル）が自動ダウンロードされる。

---

## 動作の仕組み

```
セッション開始
    ↓
gdrive-download.sh 実行
    → Google Drive から MEMORY.md を取得
    ↓
Claude Codeで作業
    ↓
セッション終了
    ↓
gdrive-upload.sh 実行
    → MEMORY.md を Google Drive に保存
```

記憶はGoogle Driveで同期されるため、**どのPCからでも同じ記憶を共有**できる。

---

## 注意事項

- `settings.local.json`（GitHubトークン等を含む）はセキュリティのためリポジトリに含めていない
- rcloneのGoogle Drive認証は各PCで個別に実施が必要
- GitHubトークンも各PCで個別に設定が必要
