#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
難易度構成ゲート（2026-08-19 新設 / 2026-08-20 全面改訂 / 2026-08-20 2軸化）。

■ 2026-08-20（第2次改訂）＝難易度を「2軸」で測る（専務指摘）
  第1次改訂で load を「手数」から「認知過程（recall/select/construct）」へ変えた。
  だが数学で「普通の計算問題を難しくする」と、手順は一つのまま(recall)で
  要素だけ増える。process 1軸だと **計算を難しくするほど recall が増え、
  応用ゲート(recall≤30%)に落ちる** という逆行が起きた。
  ＝難易度には独立した2軸があるのに、片方しか測っていなかった。

■ 難易度の2軸（認知負荷理論／Bloom・SOLO が共通して指すもの）
  ① 内容の複雑さ＝**要素相互作用性（intrinsic load）**
     一度に頭の中で関係づける要素の数。計算の項数・負×分数×かっこの複合・
     多段・複数事実の関係づけ…で上がる。**手順が一つ(recall)でも高くなりうる。**
     ★これが難易度の主軸。complexity = low / mid / high で各問に付ける。
  ② 思考の種類＝**認知過程（recall / select / construct）**
     ①の「関係づけ・構成」の側面を名づけたもの。①を上げられない
     （原子的な暗記＝漢字・年号・用語）教科では、②が難易度の主な手段になる。

■ 8/20第1次の教訓の精密化（矛盾しない）
  「手数を増やすな」は **外在的負荷（余計な手間＝busywork）** の禁止。
  **内在的負荷（本当の複雑さ）を上げるのは正当。** 混同しない。

■ 教科タイプで主軸を切り替える（difficulty_primary＝トップに宣言）
  "complexity"（計算・複合が作れる教科＝数学・理科計算・英語）
      → 主軸＝①内容の複雑さ。**recall 上限は課さない**（難しい計算は recall で応用）。
      応用 : 単純(low) ≤ 30% かつ 高複雑(high) ≥ 30% かつ 中+高 ≥ 70%
      標準 : 単純(low) ≤ 55% かつ 高複雑(high) ≥ 1問
      ※各問に complexity(low/mid/high) が必須。
  "process"（暗記が原子的な教科＝漢字・社会用語・国語文法など）
      → 主軸＝②思考の種類（複数を関係づける・説明する）。従来どおり。
      応用 : recall ≤ 30% かつ construct ≥ 15% かつ select+construct ≥ 70%
      標準 : recall ≤ 55% かつ construct ≥ 1問
      ※各問に load(recall/select/construct) が必須。
  宣言が無いときは "process"（従来挙動）で判定し、[注意] を出して宣言を促す。

■ 3区分（②の判定は“頭の中で何が起きるか”。手数は見ない）
    recall    … 使う規則・知識が一つに決まっていて、思い出せば答えが出る。
                **何手かかっても recall**。★記述式でも書く中身が想起なら recall。
    select    … 複数の既習事項が競合し、どれを使うか自分で判断する／
                2つ以上の事項を関係づける。
    construct … 初見の文脈・条件から自分で組み立てる／なぜそうなるかを説明する。

■ 偽装がはじかれる理由
    ・工程を増やす → 使う規則が1つなら recall のまま（process軸）／
      外在的負荷なので complexity も上がらない（complexity軸）
    ・配点を後半へ移す → 設問数で数えるので比率が動かない
    ・簡単な内容に select/construct のラベルだけ貼る → complexity=low が並び
      complexity軸で落ちる（数学の“中身が簡単なまま”を止める）

使い方:
    check_difficulty.py <出題履歴.json>
終了コード:
    0 = OK / skip、非0 = NG（run_checks.sh が set -e で停止する）
"""
import sys
import json

# ② 認知過程の正規化（表記ゆれ吸収）
LOAD_ALIASES = {
    "recall": "recall", "想起": "recall", "再生": "recall", "暗記": "recall",
    "select": "select", "選択": "select", "判断": "select", "関係づけ": "select",
    "関連づけ": "select", "識別": "select",
    "construct": "construct", "構成": "construct", "産出": "construct",
    "説明": "construct", "転移": "construct",
}
# ① 内容の複雑さの正規化
COMPLEXITY_ALIASES = {
    "low": "low", "低": "low", "単純": "low", "簡単": "low", "基本": "low",
    "mid": "mid", "中": "mid", "medium": "mid", "普通": "mid", "標準": "mid",
    "high": "high", "高": "high", "複雑": "high", "高複雑": "high", "発展": "high",
}
# 旧ラベル（手数基準・2026-08-20 に廃止）。見つけたら付け直しを促して停止する。
OBSOLETE = {"drill", "apply", "think", "ドリル", "応用", "思考", "論証", "統合",
            "一問一答", "用語", "複数ステップ", "条件", "場合分け", "資料", "記述"}


def norm_load(v):
    if v is None:
        return None
    s = str(v).strip()
    return LOAD_ALIASES.get(s.lower()) or LOAD_ALIASES.get(s)


def norm_complexity(v):
    if v is None:
        return None
    s = str(v).strip()
    return COMPLEXITY_ALIASES.get(s.lower()) or COMPLEXITY_ALIASES.get(s)


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


def primary_axis(d):
    """difficulty_primary を complexity/process に丸める。宣言が無ければ None。"""
    v = d.get("difficulty_primary") or d.get("difficulty_axis")
    if not v:
        return None
    s = str(v).lower()
    if any(k in s for k in ("complexity", "複雑", "内容", "計算")):
        return "complexity"
    if any(k in s for k in ("process", "種類", "思考", "認知")):
        return "process"
    return None


def gate_process(qs, bucket):
    """②思考の種類で応用/標準を判定（暗記が原子的な教科）。"""
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
        print("       recall/select/construct（認知過程）で全設問を付け直すこと。")
        return False
    if missing:
        print("  [NG] load 未設定の設問がある（recall/select/construct を必須）: "
              + " ".join(str(m) for m in missing[:20]))
        return False
    nq = sum(by.values())
    if nq == 0:
        print("  [NG] load 付きの設問が0問")
        return False
    rc, sl, cs = by["recall"], by["select"], by["construct"]
    r_pct, c_pct, h_pct = rc / nq * 100, cs / nq * 100, (sl + cs) / nq * 100
    print(f"  [軸=思考の種類] recall={rc}問({r_pct:.0f}%) / select={sl}問 / "
          f"construct={cs}問({c_pct:.0f}%) / select+construct={sl + cs}問({h_pct:.0f}%) / 設問{nq}問")
    ok = True
    if bucket == "advanced":
        if r_pct > 30 + 1e-9:
            print(f"  [NG] 応用なのに recall(想起) が {r_pct:.0f}% ＞ 上限30%。"
                  "規則を選ばせる／初見の文脈へ移す／説明させる問いに差し替えること")
            ok = False
        if c_pct < 15 - 1e-9:
            print(f"  [NG] 応用なのに construct(構成・説明) が {c_pct:.0f}% ＜ 下限15%")
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
    return ok


def gate_complexity(qs, bucket):
    """①内容の複雑さで応用/標準を判定（計算・複合が作れる教科）。recall 上限は課さない。"""
    by = {"low": 0, "mid": 0, "high": 0}
    missing = []
    for q in qs:
        cx = norm_complexity(q.get("complexity"))
        if cx is None:
            missing.append(q.get("mondai_id", "?"))
            continue
        by[cx] += 1
    if missing:
        print("  [NG] complexity 未設定の設問がある（low/mid/high を必須）: "
              + " ".join(str(m) for m in missing[:20]))
        print("       difficulty_primary=complexity の教科は各問に内容の複雑さを付けること。")
        return False
    nq = sum(by.values())
    if nq == 0:
        print("  [NG] complexity 付きの設問が0問")
        return False
    lo, mi, hi = by["low"], by["mid"], by["high"]
    lo_pct, hi_pct, mh_pct = lo / nq * 100, hi / nq * 100, (mi + hi) / nq * 100
    print(f"  [軸=内容の複雑さ] low={lo}問({lo_pct:.0f}%) / mid={mi}問 / "
          f"high={hi}問({hi_pct:.0f}%) / mid+high={mi + hi}問({mh_pct:.0f}%) / 設問{nq}問")
    ok = True
    if bucket == "advanced":
        if lo_pct > 30 + 1e-9:
            print(f"  [NG] 応用なのに 単純(low) が {lo_pct:.0f}% ＞ 上限30%。"
                  "内容そのものを難しくする（項数・負×分数×かっこの複合・多段）こと")
            ok = False
        if hi_pct < 30 - 1e-9:
            print(f"  [NG] 応用なのに 高複雑(high) が {hi_pct:.0f}% ＜ 下限30%。"
                  "余計な手間(外在的負荷)ではなく、要素相互作用性を上げること")
            ok = False
        if mh_pct < 70 - 1e-9:
            print(f"  [NG] 応用なのに 中+高 が {mh_pct:.0f}% ＜ 下限70%")
            ok = False
    elif bucket == "standard":
        if lo_pct > 55 + 1e-9:
            print(f"  [NG] 標準なのに 単純(low) が {lo_pct:.0f}% ＞ 上限55%")
            ok = False
        if hi < 1:
            print("  [NG] 標準でも 高複雑(high) が1問以上要る")
            ok = False
    return ok


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

    axis = primary_axis(d)
    if axis is None:
        axis = "process"
        print("  [注意] difficulty_primary 未宣言＝従来の『思考の種類』軸で判定する。"
              "計算・複合が作れる教科（数学・理科計算・英語）は "
              "difficulty_primary=\"complexity\" を宣言すること。")

    if axis == "complexity":
        ok = gate_complexity(qs, bucket)
    else:
        ok = gate_process(qs, bucket)

    if ok:
        print(f"  [OK] 難易度構成は {bucket}／軸={axis} の基準を満たす")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
