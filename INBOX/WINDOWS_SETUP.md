# Windows環境セットアップ（未対応項目）

## 背景

このdotfilesはLinux・Windows両環境で同じClaude Code設定を共有することを目的としている。
git pullでファイルの中身は届くが、以下の作業はgitが自動でやってくれないため手動対応が必要。

---

## 問題①：bashが動かない

Claude Codeのフック（起動時・終了時に自動実行されるスクリプト）はbashで書かれている。
WindowsにはデフォルトでBashがないため、フックが一切動かない状態だった。

**対応済み：** Git Bashをインストール済み。次回Claude Code起動時からフックが動くはず。

---

## 問題②：シンボリックリンクが未作成

このdotfilesの仕組みは「`~/.claude/`の中身をdotfilesへのショートカット（シンボリックリンク）にする」という構造になっている。Linuxでは作成済みだが、Windows側ではまだ作成されていない。

以下のリンクが必要：

```
~/.claude/settings.json                    →  ~/dotfiles/claude/settings.json
~/.claude/CLAUDE.md                        →  ~/dotfiles/CLAUDE.md
~/.claude/hooks                            →  ~/dotfiles/claude/hooks
~/.claude/scripts                          →  ~/dotfiles/claude/scripts
~/.claude/skills/brainstorming             →  ~/dotfiles/claude/skills/brainstorming
~/.claude/skills/health                    →  ~/dotfiles/claude/skills/health
~/.claude/skills/planning-with-files       →  ~/dotfiles/claude/skills/planning-with-files
~/.claude/skills/using-superpowers         →  ~/dotfiles/claude/skills/using-superpowers
~/.claude/skills/x-bookmark-to-notebooklm →  ~/dotfiles/claude/skills/x-bookmark-to-notebooklm
```

---

## 問題③：ccslが未インストール

ccslはClaude Codeの画面右下にコンテキスト使用率を表示するツール。settings.jsonに設定済みだが、ツール本体がインストールされていないと表示されない。

```
pip install ccsl
```

---

## 問題④：RTKが未インストール

RTKはClaude Codeのトークン消費を60〜90%削減するツール。フックに組み込み済みだが、本体がインストールされていないと機能しない。

```
winget install Rustlang.Rustup
# インストール後、ターミナルを再起動してから
cargo install --git https://github.com/cybozu/rtk
rtk init -g
```
