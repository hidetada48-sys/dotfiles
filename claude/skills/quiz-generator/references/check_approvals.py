#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""承認ターンの関門（2026-08-18 新設）。

背景：ステップ3の質問・ステップ4/5の承認ターンは「人間待ち」でコードから止められない、
という理由で honor system のまま放置され、実際に何度も飛ばされた（専務の再三の指摘）。
そこで「承認を得た事実を出題履歴JSONに書く」ことを義務づけ、書いていなければ配信を拒否する。
＝黙って先へ進むと、最後の配信で必ず落ちる。

出題履歴JSON に次を入れること：

  "approvals": {
    "step3_settings": {
      "asked_at": "2026-08-18",
      "answers": {"満点": 40, "時間": 20, "記述量": "標準", "難易度": "標準", "配合": "バランス"}
    },
    "step4_core_items": {"presented_at": "2026-08-18", "approved": true},
    "step5_structure":  {"presented_at": "2026-08-18", "approved": true}
  }

使い方: check_approvals.py <出題履歴JSON>
※ approvals キーそのものが無い場合は「類題集など対象外」として素通りさせない。
   模試（daimon_summary あり）は必須、それ以外は skip。
"""
import json
import sys

REQUIRED = {
    "step3_settings": "ステップ3の質問（満点・時間・記述量・難易度・配合）",
    "step4_core_items": "ステップ4の承認ターン①（コア項目リスト）",
    "step5_structure": "ステップ5の承認ターン②（テスト構成）",
}


def main():
    if len(sys.argv) < 2:
        print("使い方: check_approvals.py <出題履歴JSON>")
        return 2
    d = json.load(open(sys.argv[1], encoding="utf-8"))

    if not d.get("daimon_summary"):
        print("  [skip] daimon_summary 無し＝模試でない（類題集）ため承認関門は対象外")
        return 0

    ap = d.get("approvals")
    if not isinstance(ap, dict):
        print("[NG] approvals が無い。ステップ3の質問・ステップ4/5の承認ターンを"
              "実施し、その事実をJSONに記録すること（飛ばして配信はできない）")
        return 1

    ng = False
    for key, label in REQUIRED.items():
        blk = ap.get(key)
        if not isinstance(blk, dict):
            print(f"[NG] approvals.{key} が無い ＝ {label} を実施していない")
            ng = True
            continue
        if key == "step3_settings":
            ans = blk.get("answers")
            if not isinstance(ans, dict) or not ans:
                print(f"[NG] approvals.{key}.answers が空 ＝ {label} の回答が記録されていない")
                ng = True
            else:
                print(f"  [OK] {label} ／ 回答 {len(ans)}件")
        else:
            if blk.get("approved") is not True:
                print(f"[NG] approvals.{key}.approved が true でない ＝ {label} の承認が無い")
                ng = True
            else:
                print(f"  [OK] {label} 承認済み")

    if ng:
        print("----")
        print("[NG] 承認の記録が欠けている。専務に提示して承認を得てから記録し直すこと。")
        return 1
    print("[OK] 質問・承認ターンの記録がそろっている。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
