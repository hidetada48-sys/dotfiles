#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
難易度構成ゲート（2026-08-19 新設 / 2026-08-20 全面改訂）。

■ 2026-08-20 の改訂＝「手数」で測るのをやめる（専務指摘）
  旧版は load を「解くのに何手かかるか」で決めていた。これが誤りだった。
  手数は認知負荷でいう **外在的負荷**（作業の煩雑さ）で、学力の壁になる
  **本質的負荷**（要素どうしの絡み合い）とは別物。手数で測ると、作り手は
  「工程を増やす」方向にしか動けず、実際に英語で
  「2つの文に共通して入る1語を書かせる」＝2手だがやることは想起のまま、
  という“無理やり手数を増やしただけ”の問題が生まれた。

■ 何で測るか（教育測定の3つの枠組みが共通して指すもの）
  ・ブルーム改訂版（記憶→理解→適用→分析→評価→創造）＝認知過程の種類
  ・SOLO（単一→多要素→関係づけ→抽象化）＝要素どうしを結ぶ度合い
  ・転移の距離（近転移＝型どおり／遠転移＝初見の文脈へ当てはめる）
  → 難しさの源は「規則を自分で選ぶか」「要素を関係づけるか」「型が通じるか」の3点。
    いずれも手数とは無関係。

■ 新しい3区分（判定は“頭の中で何が起きるか”。手数は見ない）
    recall    … 使う規則・知識が一つに決まっていて、思い出せば答えが出る。
                **何手かかっても recall**（工程を増やしても難易度は上がらない）。
                ★記述式でも、書く中身が想起なら recall（「用語を説明せよ」等）。
    select    … 複数の既習事項が競合し、どれを使うか自分で判断する。
                または2つ以上の事項を関係づける。
    construct … 初見の文脈・条件から自分で組み立てる、または「なぜそうなるか」を
                説明する。答えの道筋が一つでない。
                ★記述に限らない（初見の場面を選択肢で判断させるものも入る）。
  上から順に当てはめ、当たった最上位を採る（1問＝1票）。

■ しきい値（level＝トップの難易度宣言で切替／すべて設問数比）
    応用 : recall ≤ 30% かつ construct ≥ 15% かつ select+construct ≥ 70%
    標準 : recall ≤ 55% かつ construct ≥ 1問
    基本 : チェックせず [skip]（易問中心が正しいため）

■ 偽装がはじかれる理由
    ・工程を増やす → 使う規則が1つなら recall のまま
    ・配点を後半へ移す → 設問数で数えるので比率が動かない
    ・記述を増やす → 書く中身が想起なら recall
    ・旧ラベル（drill/apply/think）を流用 → 手数基準なので [NG]。付け直しを促す

使い方:
    check_difficulty.py <出題履歴.json>
終了コード:
    0 = OK / skip、非0 = NG（run_checks.sh が set -e で停止する）
"""
import sys
import json

# 新しい負荷区分の正規化（表記ゆれ吸収）
LOAD_ALIASES = {
    "recall": "recall", "想起": "recall", "再生": "recall", "暗記": "recall",
    "select": "select", "選択": "select", "判断": "select", "関係づけ": "select",
    "関連づけ": "select", "識別": "select",
    "construct": "construct", "構成": "construct", "産出": "construct",
    "説明": "construct", "転移": "construct",
}
# 旧ラベル（手数基準・2026-08-20 に廃止）。見つけたら付け直しを促して停止する。
OBSOLETE = {"drill", "apply", "think", "ドリル", "応用", "思考", "論証", "統合",
            "一問一答", "用語", "複数ステップ", "条件", "場合分け", "資料", "記述"}


def norm_load(v):
    if v is None:
        return None
    s = str(v).strip()
    return LOAD_ALIASES.get(s.lower()) or LOAD_ALIASES.get(s)


def is_obsolete(v):
    if v is None:
        return False
    s = str(v).strip()
    return (s.lower() in OBSOLETE) or (s in OBSOLETE)


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

    by = {"recall": 0, "select": 0, "construct": 0}
    missing, old = [], []
    for q in qs:
        raw = q.get("load")
        ld = norm_load(raw)
        if ld is None:
            (old if is_obsolete(raw) else missing).append(q.get("mondai_id", "?"))
            continue
        by[ld] += 1

    if old:
        print("  [NG] 旧ラベル（drill/apply/think＝手数基準）が使われている: "
              + " ".join(str(m) for m in old[:20]))
        print("       2026-08-20 に難易度の定義を『手数』から『認知過程』へ変えた。")
        print("       recall（規則が1つに決まり思い出せば出る・何手でも recall）／")
        print("       select（競合する事項からどれを使うか判断・2つ以上を関係づける）／")
        print("       construct（初見の文脈から組み立てる・なぜそうなるかを説明する）")
        print("       で全設問を付け直すこと。")
        sys.exit(1)
    if missing:
        print("  [NG] load 未設定の設問がある（recall/select/construct を必須）: "
              + " ".join(str(m) for m in missing[:20]))
        sys.exit(1)

    nq = sum(by.values())
    if nq == 0:
        print("  [NG] load 付きの設問が0問")
        sys.exit(1)

    rc, sl, cs = by["recall"], by["select"], by["construct"]
    r_pct = rc / nq * 100
    c_pct = cs / nq * 100
    h_pct = (sl + cs) / nq * 100

    print(f"  内訳: recall={rc}問({r_pct:.0f}%) / select={sl}問 / construct={cs}問({c_pct:.0f}%)"
          f" / select+construct={sl + cs}問({h_pct:.0f}%) / 設問{nq}問")

    ok = True
    if bucket == "advanced":
        if r_pct > 30 + 1e-9:
            print(f"  [NG] 応用なのに recall(想起) が {r_pct:.0f}% ＞ 上限30%。"
                  "工程を増やすのではなく、規則を選ばせる／初見の文脈へ移す問いに差し替えること")
            ok = False
        if c_pct < 15 - 1e-9:
            print(f"  [NG] 応用なのに construct(構成・説明) が {c_pct:.0f}% ＜ 下限15%。"
                  "記述を増やす必要はない。初見の場面での判断・誤りの理由・条件からの産出を入れること")
            ok = False
        if h_pct < 70 - 1e-9:
            print(f"  [NG] 応用なのに select+construct が {h_pct:.0f}% ＜ 下限70%")
            ok = False
    elif bucket == "standard":
        if r_pct > 55 + 1e-9:
            print(f"  [NG] 標準なのに recall(想起) が {r_pct:.0f}% ＞ 上限55%")
            ok = False
        if cs < 1:
            print("  [NG] 標準でも construct(構成・説明) が1問以上要る")
            ok = False

    if ok:
        print(f"  [OK] 難易度構成は {bucket} の基準を満たす")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
