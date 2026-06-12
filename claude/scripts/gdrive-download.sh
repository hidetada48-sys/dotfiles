#!/bin/bash
# Google Driveからclaude関連ファイルをダウンロードするスクリプト
# セッション開始時に自動実行される

GDRIVE_FOLDER="gdrive:claude-sync"
LOG_FILE="/tmp/claude-sync.log"

# rcloneをPATHから探し、見つからなければWinGet経由のパスを検索
if ! command -v rclone &>/dev/null; then
  RCLONE_PATH=$(find "$HOME/AppData/Local/Microsoft/WinGet/Packages" -name "rclone.exe" 2>/dev/null | head -1)
  [ -n "$RCLONE_PATH" ] && export PATH="$PATH:$(dirname "$RCLONE_PATH")"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ダウンロード開始" >> "$LOG_FILE"

# MEMORY.mdをダウンロード（projectsディレクトリから動的にパスを取得）
MEMORY_DIR=$(ls -d "$HOME/.claude/projects/"*/memory 2>/dev/null | head -1)
if [ -z "$MEMORY_DIR" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] memoryディレクトリが見つかりません" >> "$LOG_FILE"
  exit 1
fi
rclone sync "$GDRIVE_FOLDER/memory/" "$MEMORY_DIR/" 2>> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] memoryフォルダをダウンロードしました" >> "$LOG_FILE"


# processed_ids.jsonをダウンロード（ブックマーク処理済みリストをPC間で共有）
BOOKMARK_SYNC_DIR="$HOME/.x-bookmark-sync"
mkdir -p "$BOOKMARK_SYNC_DIR"
rclone copy "$GDRIVE_FOLDER/processed_ids.json" "$BOOKMARK_SYNC_DIR/" --update 2>> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] processed_ids.jsonをダウンロードしました" >> "$LOG_FILE"

# basic-memory ノートをダウンロード（セマンティック検索の元データ）
BASIC_MEMORY_DIR="$HOME/basic-memory"
mkdir -p "$BASIC_MEMORY_DIR"
rclone sync "$GDRIVE_FOLDER/basic-memory/" "$BASIC_MEMORY_DIR" 2>> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] basic-memoryノートをダウンロードしました" >> "$LOG_FILE"

# 売上明細（生CSV）の仮置場をダウンロード（販売参謀）
# このプロジェクトがある機だけ実行する（他PCではスキップ）
SALES_PROJECT="$HOME/mino-sakura-hq"
if [ -d "$SALES_PROJECT" ]; then
  SALES_INBOX="$SALES_PROJECT/sales/inbox"
  mkdir -p "$SALES_INBOX"
  # copy --update：追加DLのみ（gdrive側もローカル側も削除しない）。
  # 二重取り込みは「台帳(master)より新しいか」で判定する（raw/は廃止＝横展開設計）。
  rclone copy "$GDRIVE_FOLDER/sales-inbox/" "$SALES_INBOX/" --update 2>> "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 売上仮置場(sales-inbox)をダウンロードしました" >> "$LOG_FILE"

  # 未取込チェックは中身判定（csv/xlsx両対応・ファイル名に依存しない）が必要なため Python に委譲する。
  # bash では xlsx の中身を読めないので、得意先コードを中身から判定する check_inbox.py に任せる。
  # 判定: inbox の各ファイルを中身判定し、得意先ごとに台帳(売上明細台帳_{コード}.csv)が
  #   無い／古い なら未取込。build_master.py が台帳を書き直すと次回起動は新着0になる。
  # SessionStart フックの stdout は Claude のコンテキストに入る（公式仕様）ので、
  # 起動時に Claude が新着に気づき、専務へ「分析しますか？」と確認できる（工程4）。
  PY=$(command -v python || command -v python3)
  if [ -n "$PY" ]; then
    ( cd "$SALES_PROJECT" && "$PY" sales/scripts/check_inbox.py )
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] python が見つからず未取込チェックをスキップ" >> "$LOG_FILE"
  fi
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ダウンロード完了" >> "$LOG_FILE"

# ツールのインストール確認（未インストールの場合に案内を表示）
MISSING_TOOLS=()

if ! command -v rtk &>/dev/null; then
  MISSING_TOOLS+=("rtk")
fi

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
  echo ""
  echo "================================================"
  echo "  [セットアップ案内] 未インストールのツールがあります"
  echo "================================================"
  for tool in "${MISSING_TOOLS[@]}"; do
    case "$tool" in
      rtk)
        echo ""
        echo "▼ RTK（Rust Token Killer）- トークン使用量を60〜90%削減"
        echo "  インストール手順："
        echo "  1. Rustをインストール:"
        echo "     curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"
        echo "  2. RTKをビルド:"
        echo "     source ~/.cargo/env"
        echo "     cargo install --git https://github.com/rtk-ai/rtk"
        echo "  3. Claude Code用にセットアップ:"
        echo "     rtk init -g"
        echo "  ※ aarch64 Linux の場合はバイナリが使えないためソースビルドが必要"
        ;;
    esac
  done
  echo ""
  echo "================================================"
  echo ""
fi
