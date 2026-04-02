#!/bin/bash
# ユーザーが「記憶して」と言ったときに記憶保存を指示するフック

# UserPromptSubmitフックのJSON入力からプロンプトを取得
INPUT=$(cat)
PROMPT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('prompt',''))" 2>/dev/null)

# 「記憶して」が含まれていたら追加指示を注入
if echo "$PROMPT" | grep -q "記憶して"; then
  cat <<'EOF'
【システム指示】ユーザーが記憶を要求しています。以下を必ず両方実行してください：

1. basic-memory（write_noteツール）にセッションの内容を詳細に保存する
   - タイトル：日付＋作業内容の概要（例：2026-04-02 Discord自動応答セットアップ）
   - 内容：作業の流れ・決定事項・発覚した問題・解決策・残課題を詳細に記述

2. ~/.claude/projects/.../memory/ のMEMORY.mdおよび関連ファイルを更新する
   - 新しい情報があれば既存ファイルを更新、または新規ファイルを作成してMEMORY.mdにポインタを追加

保存完了後、何をどこに記録したかを簡潔にユーザーに報告してください。
EOF
fi

exit 0
