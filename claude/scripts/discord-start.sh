#!/bin/bash
# Discord Bot 自動応答セッションを tmux で起動するスクリプト

SESSION_NAME="discord-bot"

# すでに起動中か確認
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "すでに起動中です。アタッチするには:"
    echo "  tmux attach -t $SESSION_NAME"
    exit 0
fi

echo "Discord Bot セッションを起動します..."

# tmuxセッションを新規作成してClaudeを起動
tmux new-session -d -s "$SESSION_NAME" \
    "cd ~/discord-bot && claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions"

echo "起動しました！"
echo ""
echo "【操作方法】"
echo "  画面を見る:  tmux attach -t $SESSION_NAME"
echo "  停止する:    bash ~/.claude/scripts/discord-stop.sh"
echo "  切り離す:    Ctrl+B → D (tmux内で)"
