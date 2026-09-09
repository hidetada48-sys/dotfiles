#!/bin/bash
# Google Driveからclaude関連ファイルをダウンロードする（SessionStartで実行）
#
# ★2026-09-09 改修（記憶が両PCで揃わない不具合）
#   旧版は memoryフォルダを `ls -d .../*/memory | head -1` で1個しか見ておらず、
#   たまたま先頭に来た別プロジェクトのフォルダだけを同期していた。
#   本命プロジェクトの記憶は一度もDriveに上がらず、逆にDrive上の別物（古いMEMORY.md）で
#   上書きされる事故も起きていた。→ プロジェクトごとにフォルダを分けて同期する方式に変更。
#   ・Drive側 : claude-sync/memory-by-project/<キー>/
#   ・キー    : PC間で共通の名前（例 root, mino-sakura-hq, dotfiles）
#   最後に「前回の取りこぼし回収アップロード」も起動する。

source "$(dirname "$0")/gdrive-sync-lib.sh"

GDRIVE_FOLDER="gdrive:claude-sync"
LOG_FILE="/tmp/claude-sync.log"
FAIL_FLAG="/tmp/claude-gdrive-upload.failed"
STAGE="$HOME/.claude/projects/_gdrive_memory"   # Driveから受ける仮置場

# rclone が無ければ、黙って終わらず画面に出して知らせる
if ! gs_find_rclone; then
  echo "[同期] rclone が見つかりません。このPCの記憶はGoogle Driveと同期されていません。"
  exit 0
fi

# API制限(403)対策・ハング防止・高速化フラグ
RFLAGS="--contimeout=15s --timeout=120s --retries=3 --low-level-retries=10 --transfers=4 --checkers=4 --fast-list"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ダウンロード開始" >> "$LOG_FILE"

# --- ① auto-memory：プロジェクト別フォルダをまとめて1回で取得し、ローカルへ振り分ける ---
mkdir -p "$STAGE"
rclone copy $RFLAGS --update "$GDRIVE_FOLDER/memory-by-project/" "$STAGE/" 2>> "$LOG_FILE"
PREFIX=$(gs_local_prefix)
if [ -z "$PREFIX" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ★このPCのプロジェクト接頭辞が不明。$STAGE に置いたままにします" >> "$LOG_FILE"
  echo "[同期] このPCのホーム設定が gdrive-sync-lib.sh に未登録です。記憶は $STAGE に置いてあります。"
else
  for KEYDIR in "$STAGE"/*/; do
    [ -d "$KEYDIR" ] || continue
    KEY=$(basename "$KEYDIR")
    if [ "$KEY" = "root" ]; then
      TARGET="$HOME/.claude/projects/$PREFIX/memory"
    else
      TARGET="$HOME/.claude/projects/$PREFIX-$KEY/memory"
    fi
    mkdir -p "$TARGET"
    # -u（新しいものだけ上書き）で、こちらの方が新しい記憶を古い記憶で潰さない
    cp -u "$KEYDIR"*.md "$TARGET/" 2>/dev/null
  done
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] memory(プロジェクト別)をダウンロードしました" >> "$LOG_FILE"
fi

# --- ② basic-memory ノート（セマンティック検索の元データ） ---
mkdir -p "$HOME/basic-memory"
rclone copy $RFLAGS --update "$GDRIVE_FOLDER/basic-memory/" "$HOME/basic-memory" 2>> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] basic-memoryノートをダウンロードしました" >> "$LOG_FILE"

# --- ③ 急がないもの（ブックマーク・生産データ仮置場・機密ファイル）は裏で取る ---
# ※販売の売上生データ（sales-inbox）のDLは 2026-09-02 に廃止（取得は業務DBから）。
EXTRA="$(dirname "$0")/gdrive-download-extra.sh"
if [ -f "$EXTRA" ]; then
  if command -v setsid >/dev/null 2>&1; then
    setsid nohup bash "$EXTRA" >/dev/null 2>&1 < /dev/null &
  else
    nohup bash "$EXTRA" >/dev/null 2>&1 < /dev/null &
  fi
  disown 2>/dev/null
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ダウンロード完了(記憶のみ・業務データは背景)" >> "$LOG_FILE"

# --- ⑤ 前回の取りこぼしを知らせる＋回収アップロードを起動（背景・セッションは止めない） ---
if [ -f "$FAIL_FLAG" ]; then
  echo "[同期] 前回のアップロードに失敗が残っています。今から再試行します（詳細: $LOG_FILE）"
fi
bash "$(dirname "$0")/gdrive-upload.sh" --force

# ツールのインストール確認（未インストールの場合に案内を表示）
if ! command -v rtk >/dev/null 2>&1; then
  echo ""
  echo "▼ RTK（Rust Token Killer）未導入 - トークン使用量を60〜90%削減できます"
  echo "  1) curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"
  echo "  2) source ~/.cargo/env && cargo install --git https://github.com/rtk-ai/rtk"
  echo "  3) rtk init -g"
  echo ""
fi
