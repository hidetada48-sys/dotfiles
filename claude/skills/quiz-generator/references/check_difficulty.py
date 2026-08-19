#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
難易度構成ゲート（2026-08-19 新設）。

■ なぜ要るか
  配点検算・答え漏れ・answer-validator は「正しいか」しか見ておらず、
  「難しいか（手応えがあるか）」を一つも見ていなかった。
  そのため簡単な計算・一問一答ばかりの模試でも全関門を素通りしていた。
  さらに「大問1・2を圧縮して後半へ配点を移動＝応用寄り」という
  “配点移動だけ”の操作は難易度を1ミリも上げないのに、
  ラベルだけ「応用」に貼り替えられてしまっていた（2026-08-19 専務叱責）。

■ 何を機械で縛るか
  各設問に負荷区分 `load` を必須で持たせ、その「設問数（問題数）の構成比」を検算する。
  ※配点比ではなく設問数比で見る（2026-08-19 改修）。配点は作り手の匙加減なので、
    配点で割ると think に高配点・drill に低配点を振るだけで割合を偽装でき、
    封じたはずの『配点移動での応用偽装』と同じ穴になるため。1問=1票で数える。
  load は「解くのに何手かかるか」で決める（format＝出題形式とは別軸）。
    - drill … 1手で終わる：単純計算・一問一答・用語の想起・定義の確認
    - apply … 複数手：複数ステップ計算・条件処理・場合分け・資料読み取り
    - think … 統合・論証：記述で理由/過程を説明・複数条件の統合・証明的な思考
  配点移動では drill の本数・配点は減らないため、この関門は
  「易しい問題を差し替える」までパスできない＝専務の意図どおりになる。

■ しきい値（level＝トップの難易度宣言で切替）
    応用（応用/発展/advanced）：drill ≤ 35% かつ apply+think ≥ 50%
    標準（標準/basic/standard）：drill ≤ 60%
    基本（基本）：チェックせず [skip]（易問中心が正しいため）
  → 応用を名乗るのに drill が 35% を超えていたら [NG] で停止し、
    「配点をいじるのではなく易問を差し替えよ」と促す。

使い方:
    check_difficulty.py <出題履歴.json>
終了コード:
    0 = OK / skip、非0 = NG（run_checks.sh が set -e で停止する）
"""
import sys
import json

# 負荷区分の正規化（表記ゆれ吸収）
LOAD_ALIASES = {
    "drill": "drill", "ドリル": "drill", "基本計算": "drill", "一問一答": "drill",
    "用語": "drill", "想起": "drill", "暗記": "drill",
    "apply": "apply", "応用": "apply", "複数ステップ": "apply", "条件": "apply",
    "場合分け": "apply", "資料": "apply",
    "think": "think", "思考": "think", "記述": "think", "論証": "think", "統合": "think",
}


def norm_load(v):
    if v is None:
        return None
    s = str(v).strip().lower()
    # 日本語はlowerで変わらないので原文でも引く
    return LOAD_ALIASES.get(s) or LOAD_ALIASES.get(str(v).strip())


def level_bucket(level):
    """トップの level 宣言を 応用/標準/基本 の3段に丸める。"""
    if not level:
        return None
    s = str(level)
    if any(k in s for k in ("応用", "発展", "advanced", "hard")):
        return "advanced"
    if any(k in s for k in ("標準", "standard", "basic", "普通")):
        return "standard"
    if "基本" in s or "easy" in s.lower():
        return "kihon"
    return None


def main():
    if len(sys.argv) < 2:
        print("使い方: check_difficulty.py <出題履歴.json>")
        sys.exit(2)
    d = json.load(open(sys.argv[1], encoding="utf-8"))

    qs = d.get("questions")
    if qs is None:
        print("  [skip] questions 無し＝類題集 or 検算対象外")
        sys.exit(0)

    bucket = level_bucket(d.get("level") or d.get("difficulty"))
    if bucket is None:
        print("  [NG] 難易度 level が宣言されていない（level に 基本/標準/応用 のいずれか）")
        sys.exit(1)
    if bucket == "kihon":
        print("  [skip] level=基本 は易問中心が正しいため難易度構成は検査しない")
        sys.exit(0)

    # ★構成比は「設問数（問題数）」で見る（2026-08-19 改修・専務指摘）。
    #   配点で割ると「think問に高い配点／drill問に低い配点」を振るだけで割合をいじれてしまい、
    #   これは封じたはずの『配点移動での“応用”偽装』とまったく同じ抜け道になる。
    #   配点はこちらの匙加減なので恣意性が残る。→ 1問=1票の設問数比で判定し、
    #   基準を満たすには“易問を実際に思考問題へ差し替える”しかない形にする。
    by = {"drill": 0, "apply": 0, "think": 0}
    missing = []
    for q in qs:
        ld = norm_load(q.get("load"))
        if ld is None:
            missing.append(q.get("mondai_id", "?"))
            continue
        by[ld] += 1

    if missing:
        print("  [NG] load 未設定の設問がある（drill/apply/think を必須）: "
              + " ".join(str(m) for m in missing[:20]))
        sys.exit(1)

    nq = by["drill"] + by["apply"] + by["think"]
    if nq == 0:
        print("  [NG] load 付きの設問が0問")
        sys.exit(1)

    drill = by["drill"]
    hard = by["apply"] + by["think"]
    dr = drill / nq * 100
    hd = hard / nq * 100

    print(f"  内訳: drill={drill}問({dr:.0f}%) / apply+think={hard}問({hd:.0f}%) / 設問{nq}問")

    ok = True
    if bucket == "advanced":
        if dr > 35 + 1e-9:
            print(f"  [NG] 応用なのに drill(易問) が {dr:.0f}% ＞ 上限35%"
                  "。配点を動かすのではなく、易問を思考問題へ差し替えること")
            ok = False
        if hd < 50 - 1e-9:
            print(f"  [NG] 応用なのに apply+think(思考) が {hd:.0f}% ＜ 下限50%")
            ok = False
    elif bucket == "standard":
        if dr > 60 + 1e-9:
            print(f"  [NG] 標準なのに drill(易問) が {dr:.0f}% ＞ 上限60%")
            ok = False

    if ok:
        print(f"  [OK] 難易度構成は {bucket} の基準を満たす")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
