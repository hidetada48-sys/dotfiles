#!/bin/bash
# 環境セットアップスクリプト
# セッション開始時・git pull 後に自動実行される
# 役割：シンボリックリンクの自動作成・hooksPath設定・未インストールツールの通知

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
      powershell.exe -Command "New-Item -ItemType Junction -Path '$(cygpath -w "$dst")' -Target '$(cygpath -w "$src")'" > /dev/null
    else
      # ファイル → ハードリンク（管理者権限不要）
      powershell.exe -Command "New-Item -ItemType HardLink -Path '$(cygpath -w "$dst")' -Target '$(cygpath -w "$src")'" > /dev/null
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

# ========================================
# git hooksPath の設定
# ========================================

# dotfilesリポジトリのgit pullで post-merge フックが走るよう設定
if [ -d "$DOTFILES/.git" ]; then
  git -C "$DOTFILES" config core.hooksPath "$DOTFILES/githooks"
fi

# ========================================
# 未インストールツールの通知
# ========================================

MISSING=()

# MCPサーバーの command を settings.json から読み取ってチェック
if [ -f "$SETTINGS" ]; then
  MCP_CMDS=$(python3 -c "
import json
try:
    d = json.load(open('$SETTINGS'))
    for v in d.get('mcpServers', {}).values():
        cmd = v.get('command', '')
        if cmd:
            print(cmd)
except:
    pass
" 2>/dev/null)
  while IFS= read -r cmd; do
    [ -z "$cmd" ] && continue
    command -v "$cmd" &>/dev/null || MISSING+=("MCP コマンド: $cmd")
  done <<< "$MCP_CMDS"
fi

# hookスクリプトの # REQUIRES: 宣言を走査してチェック
for script in "$DOTFILES/claude/hooks"/*.sh "$DOTFILES/claude/scripts"/*.sh; do
  [ -f "$script" ] || continue
  while IFS= read -r line; do
    # "# REQUIRES: tool1 tool2" 形式を解析
    [[ "$line" =~ ^#\ REQUIRES:\ (.+)$ ]] || continue
    for tool in ${BASH_REMATCH[1]}; do
      command -v "$tool" &>/dev/null || MISSING+=("$(basename "$script"): $tool")
    done
  done < "$script"
done

# 未インストールがあれば通知
if [ ${#MISSING[@]} -gt 0 ]; then
  echo ""
  echo "================================================"
  echo "  [setup] 未インストールのツールがあります"
  echo "================================================"
  for item in "${MISSING[@]}"; do
    echo "  ✗ $item"
  done
  echo "================================================"
  echo ""
fi
