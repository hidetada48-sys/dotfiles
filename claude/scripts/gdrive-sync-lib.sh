#!/bin/bash
# Google Drive同期の共通部品（upload/download の両方から読み込む）
# ★2026-09-09 新設: 「Windowsの記憶がDriveに上がらない」不具合の修正で導入。
#   従来の欠陥1: memoryフォルダを `ls -d .../*/memory | head -1` で1個しか見ておらず、
#               先頭に来た別プロジェクト（claude-mem-observer-sessions）だけを同期していた。
#               本命の記憶は一度もDriveに上がらず、逆に古い別物で上書きされていた。
#   従来の欠陥2: アップロード本体がバックグラウンドのため、SessionEnd（終了時）に起動しても
#               1分半かかる処理の途中でセッションごと殺され、Driveに届いていなかった。

# 各PCのホームに対応する「Claude Codeのプロジェクトディレクトリ名の接頭辞」。
# Claude Code はプロジェクトの絶対パスの記号を「-」に置き換えてフォルダ名にする。
#   Linux  : /home/hidetada48        → -home-hidetada48
#   Windows: C:\Users\miryo          → C--Users-miryo
# PCを増やしたらここに1行足すだけでよい。
GS_HOME_KEYS="-home-hidetada48 C--Users-miryo"

# プロジェクトフォルダ名 → PC共通の名前（キー）に変換する
# 例: -home-hidetada48-mino-sakura-hq → mino-sakura-hq
#     C--Users-miryo-mino-sakura-hq   → mino-sakura-hq （両PCで同じキーになる＝同期できる）
#     -home-hidetada48                → root
gs_canon() {
  local n="$1" p
  for p in $GS_HOME_KEYS; do
    n="${n#$p}"
  done
  n="${n#-}"
  [ -z "$n" ] && n="root"
  # 別名合わせ（2026-09-10 追加）
  #   Linux は /home/hidetada48 直下で作業＝キー "root"
  #   Windows は C:\Users\miryo\claude で作業＝キー "claude"
  #   役割は同じ（同じ MEMORY.md を共有してきた）のに名前が違うため、
  #   そのままだと記憶が2つの箱に分かれて永久に共有されない。"claude" は "root" に寄せる。
  [ "$n" = "claude" ] && n="root"
  printf '%s' "$n"
}

# キー → このPCのプロジェクトフォルダ名（gs_canon の逆変換）
# 使い方: gs_key_to_dir <キー> <接頭辞>
gs_key_to_dir() {
  local key="$1" prefix="$2"
  if [ "$key" = "root" ]; then
    # ホーム直下で作業しているPC（Linux）はそのまま
    [ -d "$HOME/.claude/projects/$prefix" ] && { printf '%s' "$prefix"; return 0; }
    # ホーム直下では作業しないPC（Windows）は claude プロジェクトが受け皿
    [ -d "$HOME/.claude/projects/$prefix-claude" ] && { printf '%s' "$prefix-claude"; return 0; }
    printf '%s' "$prefix"; return 0
  fi
  printf '%s' "$prefix-$key"
}

# このPCのプロジェクトフォルダ名の接頭辞を返す（キー→ローカルパスの逆引き用）
gs_local_prefix() {
  local p d
  for p in $GS_HOME_KEYS; do
    # 1) 完全一致：ホーム直下そのものを開いて作業したことがある場合（Linuxはこちらに当たる）
    [ -d "$HOME/.claude/projects/$p" ] && { printf '%s' "$p"; return 0; }
    # 2) 前方一致：ホーム配下のプロジェクトしか無い場合。
    #    2026-09-10 追加。Windows は C:\Users\miryo 直下で作業しないため
    #    「C--Users-miryo」というフォルダが存在せず、1) だけでは接頭辞を特定できなかった。
    #    その結果 Drive から受けた記憶が仮置場に残ったまま反映されなかった。
    for d in "$HOME/.claude/projects/$p"-*; do
      [ -d "$d" ] && { printf '%s' "$p"; return 0; }
    done
  done
  printf ''
}

# rclone を PATH から探し、無ければ WinGet 配下も探す。見つからなければ 1 を返す
gs_find_rclone() {
  if ! command -v rclone >/dev/null 2>&1; then
    local RCLONE_PATH
    RCLONE_PATH=$(find "$HOME/AppData/Local/Microsoft/WinGet/Packages" -name "rclone.exe" 2>/dev/null | head -1)
    [ -n "$RCLONE_PATH" ] && export PATH="$PATH:$(dirname "$RCLONE_PATH")"
  fi
  command -v rclone >/dev/null 2>&1
}
