#!/usr/bin/env bash
# 配布の関門（2026-08-10 新設）。
# 生成物を「HTML＋PDF＋log の3点」でDrive教材フォルダへ確実に上げるランナー。
#
# 背景：DriveのプレビューやほかのPCでは、自己完結HTMLがソース（文字の羅列）で開いて読めない。
#   ＝配布用の正はPDF。従来はPDF化＋アップロードが手作業で、数学の類似問題集で漏れた（2026-08-10）。
#   → PDF自動生成＋3点アップ＋着地検証を1本にまとめ、欠けたらエラーで止める（静かに漏らさない）。
#
# 使い方:
#   publish_to_drive.sh <html> <drive_dest> [extra_file ...]
#     <html>       … 出力HTML（絶対 or 相対パス）
#     <drive_dest> … 例 "gdrive:中1テスト対策/期末テスト_模擬類似/"
#     [extra_file] … log.json / 出題履歴.json など一緒に上げる補助ファイル（0個以上）
#
# 動作:
#   1. HTML から PDF を headless Chrome で生成（ブラウザが無ければエラー停止）
#   2. HTML＋PDF＋extra を drive_dest へ rclone copy
#   3. drive_dest を rclone lsf で読み、上げたファイルが着地したか検証。欠けたら非ゼロ終了
#
# ★このスクリプトが最後まで通れば「Driveで開ける配布物が揃った」ことが機械で保証される。
set -eo pipefail

HTML="${1:-}"; DEST="${2:-}"
if [ -z "$HTML" ] || [ -z "$DEST" ]; then
  echo "使い方: publish_to_drive.sh <html> <drive_dest> [extra_file ...]"; exit 2
fi
shift 2
EXTRAS=("$@")

if [ ! -f "$HTML" ]; then
  echo "[NG] HTMLが見つからない: $HTML"; exit 2
fi
command -v rclone >/dev/null 2>&1 || { echo "[NG] rclone が無い。Driveへ上げられない"; exit 3; }

# --- 1) headless Chrome を探す（両OS対応。無ければ止める＝PDFを黙って飛ばさない）---
find_chrome() {
  # 環境変数 CHROME で明示指定を最優先
  if [ -n "${CHROME:-}" ] && [ -x "${CHROME}" ]; then echo "$CHROME"; return 0; fi
  local c
  for c in chromium chromium-browser google-chrome google-chrome-stable chrome; do
    if command -v "$c" >/dev/null 2>&1; then command -v "$c"; return 0; fi
  done
  # Linux: playwright 同梱の chromium
  for c in "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux/chrome; do
    [ -x "$c" ] && { echo "$c"; return 0; }
  done
  # Windows(git-bash): Chrome / Edge の既定パス
  for c in \
    "/c/Program Files/Google/Chrome/Application/chrome.exe" \
    "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
    "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"; do
    [ -x "$c" ] && { echo "$c"; return 0; }
  done
  return 1
}

CHROME_BIN="$(find_chrome || true)"
if [ -z "$CHROME_BIN" ]; then
  echo "[NG] headless Chrome/Chromium/Edge が見つからない。"
  echo "     PDFを作れないので配布を中止する（HTMLだけ上げるのは禁止＝Driveで読めないため）。"
  echo "     環境変数 CHROME にブラウザのパスを指定して再実行するか、ブラウザを入れること。"
  exit 4
fi

PDF="${HTML%.html}.pdf"
echo "▼ PDF生成: $(basename "$PDF")  （$CHROME_BIN）"
"$CHROME_BIN" --headless --disable-gpu --no-sandbox \
  --print-to-pdf-no-header --print-to-pdf="$PDF" "$HTML" >/dev/null 2>&1 || true
if [ ! -s "$PDF" ]; then
  echo "[NG] PDF生成に失敗した（$PDF が空 or 無い）。配布を中止。"; exit 4
fi

# --- 2) 3点＋extra を Drive へ ---
UP=("$HTML" "$PDF")
if [ "${#EXTRAS[@]}" -gt 0 ]; then UP+=("${EXTRAS[@]}"); fi
echo "▼ Driveへコピー: $DEST"
for f in "${UP[@]}"; do
  [ -f "$f" ] || { echo "[NG] 送るファイルが無い: $f"; exit 2; }
  rclone copy "$f" "$DEST" >/dev/null
  echo "   ・$(basename "$f")"
done

# --- 3) 着地検証（欠けたら止める）---
echo "▼ 着地検証（Drive側に実在するか）"
LIST="$(rclone lsf "$DEST" 2>/dev/null || true)"
MISS=0
for f in "${UP[@]}"; do
  b="$(basename "$f")"
  if printf '%s\n' "$LIST" | grep -Fxq "$b"; then
    echo "   ✓ $b"
  else
    echo "   ✗ $b が Drive に無い"; MISS=1
  fi
done
if [ "$MISS" -ne 0 ]; then
  echo "[NG] 配布物が揃っていない。上の✗を解消するまで完了にしない。"; exit 5
fi

echo ""
echo "✅ 配布の関門クリア：HTML＋PDF＋補助ファイルがDriveに揃った。"
echo "   他PCでは PDF を開けば図表つきで読める（HTMLはプレビューだと文字の羅列になる）。"
