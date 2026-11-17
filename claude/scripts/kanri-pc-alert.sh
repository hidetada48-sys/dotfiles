#!/bin/bash
# 管理PC・販売ソフトの依頼のときに、私（Claude）あてに「業務DBの入口で自分でやる」と知らせる（UserPromptSubmit）
# 2026-11-17 専務承認「入れろ」。事例＝11/17 販売ソフトの設計ファイルを読む依頼で、昨日の単価の登録と同じ
#   業務DBの入口を使わず、管理PCで .bat を動かしてコピーする案を作り「なぜ見当違いのことを実施した」と叱責された。
# 正典＝docs/plans/2026-11-16-業務DBへの書き込み-design.md の「入口の一覧」／プロジェクトの CLAUDE.md「業務DB直結」
# 見分ける言葉＝~/.claude/scripts/kanri_pc_words.txt（漏れた言い方はそこへ1行足す）
# 専務の画面には何も出さない（標準出力は私あての知らせになる）。python が無ければ何もしない。

PROJECT="$HOME/mino-sakura-hq"
case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac
WORDS_FILE="$HOME/.claude/scripts/kanri_pc_words.txt"
[ -f "$WORDS_FILE" ] || exit 0

# Windows は python、Linux は python3（MS Store の偽物は弾く）
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) ORDER="python py python3" ;;
  *)                    ORDER="python3 python" ;;
esac
PY=""
for c in $ORDER; do
  if command -v "$c" >/dev/null 2>&1 && [ "$("$c" -c 'print(1)' 2>/dev/null)" = "1" ]; then PY="$c"; break; fi
done
[ -n "$PY" ] || exit 0

# 専務のチャットの文に、言葉の一覧のどれかがあるか（大文字・小文字は区別しない）
HIT=$(PYTHONIOENCODING=utf-8 KPC_WORDS="$WORDS_FILE" "$PY" -c 'import sys,json,os
try:
    t=json.loads(sys.stdin.buffer.read().decode("utf-8","replace")).get("prompt") or ""
except Exception:
    t=""
ws=[l.strip() for l in open(os.environ["KPC_WORDS"],encoding="utf-8") if l.strip() and not l.startswith("#")]
low=t.lower()
hit=[w for w in ws if w.lower() in low]
print("・".join(hit[:3]))' 2>/dev/null)
[ -n "$HIT" ] || exit 0

cat <<EOF

【管理PC・販売ソフトの依頼（${HIT}）】2026-11-17 専務承認の標準：
・管理PCの中の物（販売ソフトの表・D:\\magic のファイル）は、私が業務DBの入口から直接読む・書く。管理PCで .bat を動かしていただく・コピーしていただく案は出さない。
・入口＝mino_ro（表を読む・tools/db/mino_query.ps1）／mino_rw（表に書く・tools/db/mino_write.ps1）／mino_file（管理PCのファイルを読む・tools/db/mino_file_read.ps1）。
・入口が足りなければ入口を1つ足す（専務が管理者のパスワードを1回入れる。場所＝secrets/販売ソフト/2026-10-28_管理PC調査/07_magic_ini.txt の1424行目。聞かれたら即答）。
・業務の表を読む前・書く前は承認。販売ソフトのファイルを読むのは承認なし。使い方の正＝docs/plans/2026-11-16-業務DBへの書き込み-design.md「入口の一覧」。
EOF
exit 0
