#!/bin/bash
# claude関連ファイルをGoogle Driveにアップロードするスクリプト
# SessionEndフック（セッション終了時）と basic-memory 保存後（PostToolUse）に発火する。
# ※2026-06-07: 発火タイミングを Stop（毎ターン）→ SessionEnd（終了時）に変更。
#   gdrive同期は Windows との記憶共有が目的で、毎ターン走らせる必要はないため
#   「記憶を書いたとき（PostToolUse）＋セッションの区切り（SessionEnd）」だけに絞った。
#
# フリーズ対策（2026-06-06 改修）：
#   旧版は rclone をその場でブロック実行し、毎ターン約38秒固まっていた。
#   - デバウンス: 前回アップロードから一定時間内なら即スキップ（連続実行させない）
#   - バックグラウンド実行: アップロード本体を裏に回しターンを一切ブロックしない
#   - 二重起動防止ロック: 前回のアップロードが走行中なら新規起動しない
#   - rclone にタイムアウト/高速化フラグを付与（裏の処理も暴走・ハングさせない）
#   - 何があってもセッションは止めない（常に exit 0）
#   - Windows(Git Bash)/Linux 両対応

GDRIVE_FOLDER="gdrive:claude-sync"
LOG_FILE="/tmp/claude-sync.log"
STAMP_FILE="/tmp/claude-gdrive-upload.stamp"   # 前回アップロード時刻（エポック秒）
LOCK_DIR="/tmp/claude-gdrive-upload.lock"      # 二重起動防止ロック
FAIL_FLAG="/tmp/claude-gdrive-upload.failed"   # 前回アップロードに失敗が残っている印
DEBOUNCE_SEC=180                                # この秒数内の再アップロードはスキップ
LOCK_STALE_SEC=600                              # この秒数より古いロックは死骸とみなして奪う

# --- デバウンス: 直近にアップロード済みなら即終了（ターンをブロックしない） ---
NOW=$(date +%s 2>/dev/null)
if [ -n "$NOW" ] && [ -f "$STAMP_FILE" ]; then
  LAST=$(cat "$STAMP_FILE" 2>/dev/null)
  case "$LAST" in
    ''|*[!0-9]*) LAST=0 ;;   # 数値でなければ0扱い
  esac
  # ★前回に失敗が残っているときはデバウンスしない（記憶の取りこぼしを次の機会で必ず回収する）
  if [ $((NOW - LAST)) -lt "$DEBOUNCE_SEC" ] && [ ! -f "$FAIL_FLAG" ]; then
    exit 0
  fi
fi

# 今回の時刻を記録（成否に関わらずデバウンス基準を更新する）
[ -n "$NOW" ] && printf '%s' "$NOW" > "$STAMP_FILE" 2>/dev/null

# --- 実アップロードはバックグラウンドで実行（ターンを止めない） ---
(
  # 二重起動防止: ロックが取れなければ何もしない（前回処理がまだ走行中）
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    # ロックが LOCK_STALE_SEC より古ければ前回が異常終了した死骸とみなし、消して取り直す
    LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "$LOCK_DIR" 2>/dev/null || echo 0) ))
    if [ "$LOCK_AGE" -gt "$LOCK_STALE_SEC" ]; then
      rmdir "$LOCK_DIR" 2>/dev/null
      mkdir "$LOCK_DIR" 2>/dev/null || exit 0
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] 古いロックを解除して再開しました" >> "$LOG_FILE"
    else
      exit 0
    fi
  fi
  trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT  # 終了時に必ずロック解除

  # rclone を PATH から探し、無ければ WinGet 経由のパスを検索
  if ! command -v rclone >/dev/null 2>&1; then
    RCLONE_PATH=$(find "$HOME/AppData/Local/Microsoft/WinGet/Packages" -name "rclone.exe" 2>/dev/null | head -1)
    [ -n "$RCLONE_PATH" ] && export PATH="$PATH:$(dirname "$RCLONE_PATH")"
  fi
  # rclone が無ければ静かに終了（未インストール環境ではスキップ）
  command -v rclone >/dev/null 2>&1 || exit 0

  # ハング防止＆高速化フラグ（接続10秒・通信30秒で打ち切り、並列・リトライ最小）
  # ★2026-09-02 改修: Google Drive の 403 rateLimitExceeded で毎回失敗していたため見直した。
  #   --fast-list       : ディレクトリ一覧のAPI呼び出しを激減させる（クォータ超過の最大要因を潰す）
  #   --retries/--low-level-retries : 1回で諦めず再試行する（旧設定は1回で即失敗＝記憶が上がらない）
  #   --drive-pacer-*   : 429/403が出たとき自動で間隔を空ける
  #   --transfers/--checkers を8→4に下げ、同時API数を抑える
  RFLAGS="--contimeout=15s --timeout=120s --retries=3 --low-level-retries=10 --transfers=4 --checkers=4 --fast-list --drive-pacer-min-sleep=100ms --drive-pacer-burst=20"

  # rclone を実行し、成否をログに「正直に」記録する（失敗を「成功」と書かない）。
  # 旧版は exit code を見ずに必ず「アップロードしました」と書いていたため、
  # 機密データの同期が失敗しても気づけなかった（2026-06-18 改修）。
  # 使い方: run_rclone "ラベル" copy $RFLAGS --update 送信元 送信先
  # ★sync（ミラー）は使わない（2026-08-20 改修）。sync は「送信先にあって送信元に無いファイル」を
  # 消すため、片方のPCが欠けた状態でアップロードすると、もう片方のPCが作った記録がDriveから消える。
  # 実際に労災ケースの原本が1件消えた。copy + --update なら削除は伝播せず、新しい方だけが残る。
  run_rclone() {
    local label="$1"; shift
    rclone "$@" 2>> "$LOG_FILE"
    local rc=$?
    if [ "$rc" -eq 0 ]; then
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${label}をアップロードしました" >> "$LOG_FILE"
    else
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] ★失敗: ${label} のアップロードに失敗しました (rclone rc=$rc)" >> "$LOG_FILE"
      touch "$FAIL_FLAG" 2>/dev/null   # 失敗の印。次回はデバウンスを無視して再試行される
    fi
  }

  rm -f "$FAIL_FLAG" 2>/dev/null   # 今回の実行分の判定を始めるので、いったん印を消す

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] アップロード開始(背景)" >> "$LOG_FILE"

  # メモリフォルダごとアップロード（MEMORY.md + 個別メモリファイル全て）
  MEMORY_DIR=$(ls -d "$HOME/.claude/projects/"*/memory 2>/dev/null | head -1)
  if [ -d "$MEMORY_DIR" ]; then
    run_rclone "memoryフォルダ" copy $RFLAGS --update "$MEMORY_DIR" "$GDRIVE_FOLDER/memory/"
  fi

  # processed_ids.json をアップロード（ブックマーク処理済みリストをPC間で共有）
  PROCESSED_IDS_FILE="$HOME/.x-bookmark-sync/processed_ids.json"
  if [ -f "$PROCESSED_IDS_FILE" ]; then
    run_rclone "processed_ids.json" copy $RFLAGS "$PROCESSED_IDS_FILE" "$GDRIVE_FOLDER/"
  fi

  # basic-memory ノートをアップロード（セマンティック検索の元データ）
  BASIC_MEMORY_DIR="$HOME/basic-memory"
  if [ -d "$BASIC_MEMORY_DIR" ]; then
    # ★--update 必須: これが無いと、こちらの古いノートで Drive 上の新しいノート（別PCが書いたもの）を上書きしてしまう
    run_rclone "basic-memoryノート" copy $RFLAGS --update "$BASIC_MEMORY_DIR" "$GDRIVE_FOLDER/basic-memory/"
  fi

  # 機密ファイル（secrets/hr/）をアップロード（社員台帳・有給付与一覧など）
  SALES_PROJECT="$HOME/mino-sakura-hq"
  SECRETS_HR="$SALES_PROJECT/secrets/hr"
  if [ -d "$SECRETS_HR" ]; then
    run_rclone "secrets/hr（機密）" copy $RFLAGS --update "$SECRETS_HR/" "$GDRIVE_FOLDER/secrets-hr/"
  fi

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] アップロード完了(背景)" >> "$LOG_FILE"
) >/dev/null 2>&1 &

# バックグラウンドジョブを親から切り離してフックを即終了（セッションを止めない）
disown 2>/dev/null

exit 0
