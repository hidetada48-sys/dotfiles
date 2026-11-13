#!/bin/bash
# 定例業務の実施状況（SessionStart）＝起動時の通知を1本にまとめたもの（2026-10-04 専務承認）
# 役割：定例業務 24件（focus/定例業務/定例業務の台帳.csv）を判定し、月ごとの表を書き直して、要対応を Claude に知らせる。
#       これまでの12本（週初回・法改正・年次行事・有給・販売の月次・ジャンボ・在庫・生産日誌・日報・A重油・運賃・月次データ）を置き換える。
# 正典：docs/plans/2026-10-04-定例業務の通知の一覧（改修後）.md／CLAUDE.md 行動ルール0-10
# 判定は tools/teirei.py。python が無ければ「判定できません」と出す（黙らない）。

#
# ★定例業務を出す日と場面（2026-11-14 専務承認「案2でよい　その上で、土日は定例を求めたとき以外は定例を出さない」・控え帳 11/14 7:39）
#   月曜        ＝その日の最初の起動で出す（定例業務の2行＋表のリンク＋目次のリンク）
#   火曜〜金曜  ＝起動では出さない。専務のチャットに「目次」か「定例」があれば、その場で判定して出す
#   土曜・日曜  ＝起動では出さない。専務のチャットに「定例」があるときだけ出す（「目次」だけでは出さない）
# 使い方：引数なし＝起動時（SessionStart）／ --prompt ＝専務のチャットを受けたとき（UserPromptSubmit・入力は標準入力の JSON）

MODE="$1"
PROJECT="$HOME/mino-sakura-hq"
case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac
cd "$PROJECT" || exit 0
[ -f tools/teirei.py ] || exit 0

DOW=${TEIREI_TEST_DOW:-$(date +%u)}   # 曜日（1＝月曜 … 6＝土曜・7＝日曜）。TEIREI_TEST_DOW は試験で曜日を指定するときだけ使う
TODAY=$(date +%Y-%m-%d)
MOKUJI_URL="http://127.0.0.1:8830/index.html"

# Windows は python、Linux は python3（MS Store の偽物は弾く）
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) ORDER="python py python3" ;;
  *)                    ORDER="python3 python" ;;
esac
PY=""
for c in $ORDER; do
  if command -v "$c" >/dev/null 2>&1 && [ "$("$c" -c 'print(1)' 2>/dev/null)" = "1" ]; then PY="$c"; break; fi
done

if [ "$MODE" = "--prompt" ]; then
  # 専務のチャットに「目次」「定例」があるかを見る（python が無ければ判断できないので何もしない）
  [ -n "$PY" ] || exit 0
  WORDS=$("$PY" -c 'import sys,json
try:
    t=json.loads(sys.stdin.buffer.read().decode("utf-8","replace")).get("prompt") or ""
except Exception:
    t=""
w=[]
if "定例" in t: w.append("TEIREI")
if "目次" in t: w.append("MOKUJI")
print(" ".join(w))' 2>/dev/null)
  ASK_TEIREI=0; ASK_MOKUJI=0
  case " $WORDS " in *" TEIREI "*) ASK_TEIREI=1 ;; esac
  case " $WORDS " in *" MOKUJI "*) ASK_MOKUJI=1 ;; esac
  # 土日は「定例」のときだけ。平日は「目次」でも出す
  if [ "$ASK_TEIREI" = 1 ]; then :
  elif [ "$ASK_MOKUJI" = 1 ] && [ "$DOW" -le 5 ]; then :
  else exit 0
  fi
  echo ""
  if [ "$ASK_MOKUJI" = 1 ]; then
    echo "【定例業務】専務が目次を求めたので、定例業務をいま判定し直した（2026-11-14 専務承認）。返答には、目次のリンク（$MOKUJI_URL）と一緒に、下の定例業務の2行（要対応の件数＋表のリンク）を必ず出す。"
  else
    echo "【定例業務】専務が定例業務を求めたので、いま判定し直した。返答には下の定例業務の2行（要対応の件数＋表のリンク）を出す。"
  fi
else
  # 起動時：月曜以外は定例業務を出さない
  if [ "$DOW" -ne 1 ]; then
    if [ "$DOW" -le 5 ]; then
      echo "【定例業務】今日は月曜ではないので、起動時に定例業務を出さない。専務のチャットに「目次」か「定例」があったときだけ、その場で判定して出す（2026-11-14 専務承認）。"
    else
      echo "【定例業務】今日は土日なので、起動時に定例業務を出さない。専務のチャットに「定例」があったときだけ、その場で判定して出す（「目次」だけでは出さない・2026-11-14 専務承認）。"
    fi
    exit 0
  fi

  # ★月曜は、その日の最初の起動だけ通知する（2026-11-03 専務承認・控え帳 11/3「作業のたびに出る　初回起動のみでいい」）
  # 会話を始めるたび（起動・新しい会話・再開・/compact）にこのフックが動くため、通知した日付をパソコンごとに控え、
  # 同じ日の2回目以降は表づくり・サーバーからのコピーを行わず、Claude あての1行だけを渡して終える
  STAMP="$HOME/.claude/state/teirei_notified.txt"
  if [ -f "$STAMP" ] && [ "$(cat "$STAMP" 2>/dev/null)" = "$TODAY" ]; then
    echo "【定例業務】本日（$TODAY・月曜）の通知は、その日の最初の起動で済み。チャットに定例業務の2行を出さない（専務のチャットに「目次」か「定例」があれば、その場で判定して出る）。"
    exit 0
  fi
  mkdir -p "$HOME/.claude/state" 2>/dev/null
  echo "$TODAY" > "$STAMP" 2>/dev/null

  # 起動モードの案内（これまで週初回チェックが出していたもの）
  echo ""
  echo "【起動モード】専務モード(業務) / 裏方モード(仕組みづくり) / 休日モード。未宣言なら専務モードとみなす。"
  echo "  ※裏方・休日モードなら、下の定例業務は実行しない（次の専務モード起動で実施）。"
  echo "  ※【専務モードは毎回】当日の残作業一覧（focus/残作業一覧/残作業一覧_{今日}.md）を作り、チャットは下の定例業務の2行と目次のリンク（$MOKUJI_URL）を出す（残作業一覧は表の1番から開く。CLAUDE.md 行動ルール0-3・0-10）。"
fi

# ここから下は定例業務の判定（月曜の最初の起動／「目次」「定例」を受けたとき）
if [ -z "$PY" ]; then
  echo ""
  echo "========== 定例業務 =========="
  echo "  判定できませんでした（python がありません）。→ 【Claudeへ】専務に「定例業務を判定できませんでした」と1行で伝える。"
  echo "=============================="
  exit 0
fi

# 日報アプリの確定データ（社内サーバー）をリポジトリへコピーしてから判定する（届かなければ何もしない）
if [ -f production/scripts/nippo_server_pull.py ]; then
  PULL=$(PYTHONIOENCODING=utf-8 "$PY" production/scripts/nippo_server_pull.py 2>/dev/null)
  [ -n "$PULL" ] && { echo ""; echo "========== 日報の確定データ =========="; echo "$PULL"; }
fi

# クレーム登録アプリの台帳（社内サーバーの共用フォルダ）をリポジトリへコピーしてエクセルを作り直す（届かなければ何もしない・2026-10-26 専務承認）
if [ -f clients/scripts/claim_server_pull.py ]; then
  CLAIM=$(PYTHONIOENCODING=utf-8 "$PY" clients/scripts/claim_server_pull.py 2>/dev/null)
  [ -n "$CLAIM" ] && { echo ""; echo "========== クレーム台帳 =========="; echo "$CLAIM"; }
fi

# 運賃照合アプリが共用フォルダに作った照合表・請求書・売上明細をリポジトリへコピーしてから判定する（届かなければ何もしない・2026-11-09 専務「エスラインから作れ」）
if [ -f finance/scripts/unchin_server_pull.py ]; then
  UNCHIN=$(PYTHONIOENCODING=utf-8 "$PY" finance/scripts/unchin_server_pull.py 2>/dev/null)
  [ -n "$UNCHIN" ] && { echo ""; echo "========== 運賃照合 =========="; echo "$UNCHIN"; }
fi

# .xls を読む部品（xlrd）が無ければ uv で足して流す
if "$PY" -c 'import xlrd, openpyxl' >/dev/null 2>&1; then
  PYTHONIOENCODING=utf-8 "$PY" tools/teirei.py 2>/dev/null
elif command -v uv >/dev/null 2>&1; then
  PYTHONIOENCODING=utf-8 uv run -q --with xlrd --with openpyxl --no-project python tools/teirei.py 2>/dev/null
else
  PYTHONIOENCODING=utf-8 "$PY" tools/teirei.py 2>/dev/null
fi
exit 0
