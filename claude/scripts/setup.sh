#!/bin/bash
# 環境セットアップスクリプト
# セッション開始時に自動実行される
# 役割：シンボリックリンクの自動作成・必要ツールの自動インストール

DOTFILES="$HOME/dotfiles"
CLAUDE="$HOME/.claude"

# ========================================
# シンボリックリンクの自動作成
# ========================================

# リンクを作成する関数（OS別に対応）
create_link() {
  local src="$1"
  local dst="$2"

  # ソースが存在しない場合はスキップ
  [ ! -e "$src" ] && return

  # すでにリンク済みならスキップ
  [ -L "$dst" ] && return

  if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows（Git Bash）の場合
    # 実ディレクトリ・ファイルが邪魔していれば事前に削除
    if [ -e "$dst" ]; then
      rm -rf "$dst"
      echo "[setup] 既存を削除: $dst"
    fi

    if [ -d "$src" ]; then
      # ディレクトリ → ジャンクション（管理者権限不要）
      cmd /c mklink /J "$(cygpath -w "$dst")" "$(cygpath -w "$src")" > /dev/null
    else
      # ファイル → ハードリンク（管理者権限不要）
      cmd /c mklink /H "$(cygpath -w "$dst")" "$(cygpath -w "$src")" > /dev/null
    fi
    echo "[setup] リンク作成: $dst"
  else
    # Linux / macOS の場合（従来通り）
    if [ ! -e "$dst" ]; then
      ln -s "$src" "$dst"
      echo "[setup] リンク作成: $dst"
    fi
  fi
}

# settings.json
create_link "$DOTFILES/claude/settings.json" "$CLAUDE/settings.json"

# CLAUDE.md
create_link "$DOTFILES/CLAUDE.md" "$CLAUDE/CLAUDE.md"

# hooks ディレクトリ
create_link "$DOTFILES/claude/hooks" "$CLAUDE/hooks"

# scripts ディレクトリ（自分自身が入っているディレクトリだが念のためチェック）
create_link "$DOTFILES/claude/scripts" "$CLAUDE/scripts"

# skills 配下を全スキル自動検出してリンク作成
mkdir -p "$CLAUDE/skills"
for skill_dir in "$DOTFILES/claude/skills"/*/; do
  skill_name=$(basename "$skill_dir")
  create_link "$skill_dir" "$CLAUDE/skills/$skill_name"
done

# ========================================
# 必要ツールの自動インストール
# ========================================

# settings.jsonのstatusLineコマンドを読み取って未インストールなら自動インストール
SETTINGS="$CLAUDE/settings.json"
if [ -f "$SETTINGS" ]; then
  STATUS_CMD=$(python3 -c "import json; d=json.load(open('$SETTINGS')); print(d.get('statusLine', {}).get('command', ''))" 2>/dev/null)
  if [ -n "$STATUS_CMD" ] && ! command -v "$STATUS_CMD" &>/dev/null; then
    echo "[setup] $STATUS_CMD が未インストール → pip install $STATUS_CMD"
    pip install "$STATUS_CMD" --quiet --break-system-packages 2>/dev/null \
      || pip install "$STATUS_CMD" --quiet 2>/dev/null
  fi
fi
