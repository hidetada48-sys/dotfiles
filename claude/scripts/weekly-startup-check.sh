#!/bin/bash
# 週初回起動チェック（SessionStart）
# 役割：CLAUDE.md 行動ルール0-2の①②③④を、ファイルの有無だけで機械判定し、
#       未実施のステップを明示チェックリストで耳打ちする。判定からmodelの裁量を排除する。
# 設計思想：フック内ではweb調査もブロッキングpullもしない（事実通知のみ＝フリーズ防止）。
#           python3に依存しない純bash（Linux / Windows git-bash 共通で動く）。
# 全ステップ実施済みなら何も出さない（monday-startup-be-quiet：静かに）。

PROJECT="$HOME/mino-sakura-hq"

# このプロジェクト内で起動したときだけ動く
case "$PWD" in
  "$PROJECT"|"$PROJECT"/*) ;;
  *) exit 0 ;;
esac

cd "$PROJECT" || exit 0

# --- 起動モード確認（毎回・最優先）---
# CLAUDE.md「起動モード（専務／裏方）」の分岐を、文章ルール任せにせず起動時に必ず明示する。
# 週初回ゲートが全部済みで静かに終了する週でも、モードだけは毎回目に入れて素通りを防ぐ。
echo ""
echo "【起動モード】専務モード(業務) / 裏方モード(仕組みづくり)。未宣言なら専務モードとみなす。"
echo "  ※裏方モードなら、下記の週初回チェック等の週次フローは実行しないこと（次の専務モード起動で実施）。"

# --- 日付の算出（日本時間・月曜起点） ---
TODAY=$(TZ=Asia/Tokyo date +%Y-%m-%d)
DOW=$(TZ=Asia/Tokyo date +%u)                                   # 1=月 .. 7=日
THIS_MON=$(TZ=Asia/Tokyo date -d "$TODAY -$((DOW-1)) days" +%Y-%m-%d 2>/dev/null)
LAST_MON=$(TZ=Asia/Tokyo date -d "$THIS_MON -7 days" +%Y-%m-%d 2>/dev/null)
THIS_MONTH=$(TZ=Asia/Tokyo date +%Y-%m)

# date -d が使えない環境では誤検知を避けて黙って降りる
[ -n "$THIS_MON" ] || exit 0

PENDING=()
LINES=()

# ① 業界調査：今週の月曜の週次レポートが在るか
if [ -f "intelligence/reports/${THIS_MON}_weekly.md" ]; then
  LINES+=("① 業界調査   : 済 (intelligence/reports/${THIS_MON}_weekly.md)")
else
  LINES+=("① 業界調査   : 未 → intelligence-weekly スキルで生成")
  PENDING+=("①業界調査")
fi

# ② 振り返り：先週分の週次ダイジェストが保存済みか
if [ -f "reviews/${LAST_MON}_週次.md" ]; then
  LINES+=("② 振り返り   : 済 (reviews/${LAST_MON}_週次.md)")
else
  LINES+=("② 振り返り   : 未 → weekly-review スキルで先週分を保存")
  PENDING+=("②振り返り")
fi

# ③ フォーカス：今週のフォーカスの最終見直し日が今週（月曜以降）か
FOCUS_DATE=$(grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' focus/THIS_WEEK.md 2>/dev/null | head -1)
if [ -n "$FOCUS_DATE" ] && [ ! "$FOCUS_DATE" \< "$THIS_MON" ]; then
  LINES+=("③ フォーカス : 済 (最終見直し $FOCUS_DATE)")
else
  LINES+=("③ フォーカス : 未 → weekly-focus スキルで今週分を見直し")
  PENDING+=("③フォーカス")
fi

# ④ 法改正監視（月1回）：今月分のレポートが在るか
if [ -f "hr/reports/${THIS_MONTH}_法改正.md" ]; then
  LINES+=("④ 法改正監視 : 済 (hr/reports/${THIS_MONTH}_法改正.md)")
else
  LINES+=("④ 法改正監視 : 未 → hr-law-watch スキルで今月分を調査")
  PENDING+=("④法改正監視")
fi

# 未実施が1件も無ければ静かに終了
[ ${#PENDING[@]} -eq 0 ] && exit 0

echo ""
echo "========== 週初回起動チェック（CLAUDE.md ルール0-2）=========="
echo "  ※【専務モード限定】裏方モードなら下記は実行しない（次の専務モード起動で実施）。"
for l in "${LINES[@]}"; do echo "  $l"; done
echo "  ------------------------------------------------------------"
echo "  未実施: ${PENDING[*]}"
echo "  → 「調査→振り返り→フォーカス→法改正監視」の順で、上記「未」を実施すること。"
echo "  （法改正の報告は他の一覧の後に出す。①で生成したレポートを②③に反映する）"
echo "============================================================"
echo ""
