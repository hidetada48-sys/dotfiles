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

# DEST にリモート指定（例 gdrive:）が無ければ既定リモートを補完する（2026-08-13 修正）。
#   これが無いと rclone は remote 無しパスを「ローカル」とみなし、
#   ./中1テスト対策/… へ静かにコピー→同じローカルを lsf して「着地✓」＝偽陽性になる
#   （2026-08-13 に実際に発生。gdrive: を付け忘れて未アップなのに✓が出た）。
#   先頭が「名前:」でなければ ${RCLONE_REMOTE:-gdrive}: を前置。remote 名が違う環境では
#   rclone がリモート未定義で明確に失敗する＝黙ってローカルへ落ちる事故より安全。
if ! printf '%s' "$DEST" | grep -qE '^[A-Za-z0-9_-]+:'; then
  DEST="${RCLONE_REMOTE:-gdrive}:$DEST"
  echo "▼ DEST にリモート指定が無いため補完: $DEST"
fi

if [ ! -f "$HTML" ]; then
  echo "[NG] HTMLが見つからない: $HTML"; exit 2
fi
command -v rclone >/dev/null 2>&1 || { echo "[NG] rclone が無い。Driveへ上げられない"; exit 3; }

# --- 0) 機械の関門を先に通す（2026-08-11 追加）---
#   カバレッジ（全範囲読了）・答え漏れ・つまずき の3関門を run_checks.sh でまとめて通す。
#   extra に .json（log.json / 出題履歴.json）があれば渡す＝カバレッジとつまずきも検査される。
#   ここで非ゼロなら set -e により配布を中止＝サボると配布で止まる。
REF="$(cd "$(dirname "$0")" && pwd)"
LOG_JSON=""
for f in "${EXTRAS[@]}"; do
  case "$f" in *.json) LOG_JSON="$f"; break;; esac
done
echo "▼ 配布前の機械の関門（run_checks.sh）"
if [ -n "$LOG_JSON" ]; then
  bash "$REF/run_checks.sh" "$HTML" "$LOG_JSON"
else
  echo "  ※ .json（log/出題履歴）が渡されていない＝カバレッジ・つまずき検査は省略。"
  echo "    問題集・模試は必ず log を一緒に渡すこと（漏れ検査だけでは①②を担保できない）。"
  bash "$REF/run_checks.sh" "$HTML"
fi
echo ""

# --- 0.5) answer-validator 合格スタンプの照合（2026-08-13 恒久ゲート）---
#   answer-validator を通し av_stamp.py で発行したスタンプ <html>.av.json が、
#   いま配信するHTMLの sha256 と一致し status=pass でなければ配信を拒否する。
#   ＝「answer-validator を飛ばす」「検証後にHTMLを直す」が物理的にできなくなる（2026-08-13 専務指示）。
PYBIN="$(command -v python3 || command -v python)"
AV="$HTML.av.json"
if [ ! -f "$AV" ]; then
  echo "[NG] answer-validator 合格スタンプが無い（$AV）。"
  echo "     answer-validator スキルで全問を検証し、最後に次を実行してから配信すること："
  echo "       $PYBIN \"$REF/av_stamp.py\" \"$HTML\" \"$LOG_JSON\""
  exit 6
fi
STAMP_STATUS="$("$PYBIN" -c 'import json,sys;print(json.load(open(sys.argv[1])).get("status",""))' "$AV")"
STAMP_SHA="$("$PYBIN" -c 'import json,sys;print(json.load(open(sys.argv[1])).get("sha256",""))' "$AV")"
CUR_SHA="$("$PYBIN" -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$HTML")"
if [ "$STAMP_STATUS" != "pass" ]; then
  echo "[NG] 合格スタンプが pass ではない。answer-validator を通し直すこと。"; exit 6
fi
if [ "$STAMP_SHA" != "$CUR_SHA" ]; then
  echo "[NG] 合格スタンプの sha256 が現HTMLと一致しない＝検証後にHTMLが変わっている。"
  echo "     answer-validator を通し直し、av_stamp.py を再発行してから配信すること。"; exit 6
fi
echo "▼ answer-validator 合格スタンプ照合：OK（sha256一致・status=pass）"
echo ""

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
