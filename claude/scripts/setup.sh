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
# git hooksPath の設定
# ========================================

# dotfilesリポジトリのgit pullで post-merge フックが走るよう設定
if [ -d "$DOTFILES/.git" ]; then
  git -C "$DOTFILES" config core.hooksPath "$DOTFILES/githooks"
fi

# ========================================
# 未インストールツールの通知
# ========================================

SETTINGS="$CLAUDE/settings.json"
MISSING=()

# MCPサーバーの command を settings.json から読み取ってチェック
if [ -f "$SETTINGS" ]; then
  # python3→python→py の順でフォールバック（Linux=python3 / Windows=python）
  _PY=""
  for _c in python3 python py; do
    if command -v "$_c" >/dev/null 2>&1 && "$_c" -c "" >/dev/null 2>&1; then _PY="$_c"; break; fi
  done
  MCP_CMDS=$([ -n "$_PY" ] && "$_PY" -c "
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
      case "$tool" in
        python3|python|py)
          # pythonは名前がOSで違う（Linux=python3 / Windows=python・py）。
          # 実際に起動できる実体があれば満たすとみなす（MS Storeスタブは -c "" が失敗して弾かれる）。
          _py_ok=0
          for c in python3 python py; do
            if command -v "$c" >/dev/null 2>&1 && "$c" -c "" >/dev/null 2>&1; then _py_ok=1; break; fi
          done
          [ "$_py_ok" = 1 ] || MISSING+=("$(basename "$script"): python(python3/python/py のいずれか)")
          ;;
        *)
          command -v "$tool" &>/dev/null || MISSING+=("$(basename "$script"): $tool")
          ;;
      esac
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

# ========================================
# dotfiles の取り込み漏れ（環境ドリフト）の検知
# ========================================
# ★2026-09-09 追加: 片方のPCで直したスクリプトを、もう片方が git pull していないと
#   同じ不具合が延々と再発する（記憶がDriveに上がらない不具合の再発要因そのもの）。
#   セッション開始時に「遅れているか」だけ見て知らせる。pull は自動でやらない
#   （未コミットの変更を勝手に巻き込まないため）。
if [ -d "$DOTFILES/.git" ] && command -v git >/dev/null 2>&1; then
  timeout 10 git -C "$DOTFILES" fetch --quiet 2>/dev/null
  BEHIND=$(git -C "$DOTFILES" rev-list --count HEAD..@{u} 2>/dev/null)
  if [ -n "$BEHIND" ] && [ "$BEHIND" -gt 0 ] 2>/dev/null; then
    echo "[setup] dotfiles が $BEHIND コミット遅れています。'git -C ~/dotfiles pull' で最新のスクリプトを取り込んでください。"
  fi
fi
