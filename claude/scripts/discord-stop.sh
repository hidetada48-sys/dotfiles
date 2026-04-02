#!/bin/bash
# Discord Bot セッションを停止するスクリプト

SESSION_NAME="discord-bot"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    tmux kill-session -t "$SESSION_NAME"
    echo "Discord Bot を停止しました。"
else
    echo "Discord Bot は起動していません。"
fi
