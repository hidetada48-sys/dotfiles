# dotfiles

Claude Codeの設定と、複数PC間でのメモリ同期の仕組みを管理するリポジトリ。

## 構成

```
dotfiles/
├── CLAUDE.md                    # Claude Codeへの個人ルール
└── claude/
      ├── settings.json          # フック設定（セッション開始/終了時の同期）
      └── scripts/
            ├── gdrive-download.sh  # セッション開始時にGoogle Driveからダウンロード
            └── gdrive-upload.sh    # セッション終了時にGoogle Driveへアップロード
```

## メモリ同期の仕組み

Claude Codeのセッション開始・終了時にGoogle Driveと自動同期することで、複数PC間でメモリを共有する。

```
PC-A でセッション終了 → Google Driveへアップロード
PC-B でセッション開始 → Google Driveからダウンロード
```

同期対象：
- `MEMORY.md` — Claude Codeの作業メモリ
- `claude-mem.db` — claude-memプラグインのデータベース

---

## 別PCでのセットアップ手順

### 前提条件

以下がインストール済みであること。

- [Claude Code](https://claude.ai/code)
- [rclone](https://rclone.org/)
- git

### 手順

**① dotfiles をクローン**

```bash
git clone https://github.com/ユーザー名/dotfiles.git ~/dotfiles
```

**② rclone でGoogle Driveを認証**

```bash
rclone config
```

対話形式で設定する。以下の点に注意：
- リモート名は `gdrive` にする
- タイプは `drive`（Google Drive）を選ぶ
- ブラウザでGoogleアカウントの認証が必要

**③ シンボリックリンクを貼る**

```bash
ln -s ~/dotfiles/claude/scripts ~/.claude/scripts
ln -s ~/dotfiles/claude/settings.json ~/.claude/settings.json
```

**④ 動作確認**

```bash
# Google Driveから手動でダウンロード
bash ~/.claude/scripts/gdrive-download.sh

# ログを確認
cat /tmp/claude-sync.log
```

`ダウンロード完了` と表示されれば成功。次回 Claude Code 起動時から自動で同期される。
