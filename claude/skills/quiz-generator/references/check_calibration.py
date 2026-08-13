"""期末模試が「中間本番の分析＝設計ブリーフ」を反映して作られたかを機械で担保する。

2026-08-13 新設。背景＝中間本番の分析から得た「期末模試への反映方針」を、
期末模試を実際に作るまで“私の記憶”で保持しようとすると、コンテキスト圧縮や
別セッションで失われる。文章の申し送りでは飛ばせてしまう（feedback_machine_gate_over_prose）。
そこで av_stamp と同じ発想で、**配信の1点で機械強制**する。

しくみ:
  - 教科ごとの設計ブリーフ（例 holiday/期末模試_設計ブリーフ/数学.md）が一次保管。
  - 期末模試の出題履歴JSONに
        "design_brief_required": true
        "design_brief_sha256": "<ブリーフの sha256>"
    を持たせる。
  - 配信時に DESIGN_BRIEF=<ブリーフのパス> を渡すと、本スクリプトが
    ブリーフの sha256 と出題履歴JSONの design_brief_sha256 を照合する。
    一致しなければ（＝方針未反映・ブリーフ改変・別物）配信を拒否する。

使い方:
    python check_calibration.py <出題履歴JSON> [設計ブリーフ.md]
    （設計ブリーフは環境変数 DESIGN_BRIEF でも渡せる。引数優先）

判定:
  - JSON が模試でない（"questions" が無い）        → [skip] 0
  - design_brief_required が真でない/無い          → [skip] 0（従来どおり・後方互換）
  - 真なのにブリーフ未指定/不存在                  → [NG] 1
  - 真だが design_brief_sha256 が無い/空           → [NG] 1
  - sha256 不一致                                  → [NG] 1
  - 一致                                           → [OK] 0
"""
import hashlib
import json
import os
import sys


def sha256_of(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def check(json_path, brief_path):
    doc = json.load(open(json_path, encoding='utf-8'))

    if 'questions' not in doc:
        print('[skip] 模試の出題履歴JSONではない（"questions"なし）＝設計ブリーフ照合の対象外。')
        return 0

    required = bool(doc.get('design_brief_required'))
    if not required:
        print('[skip] design_brief_required が立っていない＝ブリーフ照合を要求しない模試。')
        return 0

    subject = doc.get('subject', '不明')
    declared = str(doc.get('design_brief_sha256', '')).strip().lower()
    print(f'教科: {subject} / design_brief_required: true')

    if not declared:
        print('[NG] design_brief_required=true なのに design_brief_sha256 が無い/空。'
              '設計ブリーフの sha256 を出題履歴JSONに入れること。')
        return 1

    if not brief_path:
        print('[NG] 設計ブリーフが渡されていない（引数 or 環境変数 DESIGN_BRIEF）。'
              '期末模試は必ず対応教科のブリーフを渡して配信すること。')
        return 1
    if not os.path.isfile(brief_path):
        print(f'[NG] 設計ブリーフが見つからない: {brief_path}')
        return 1

    actual = sha256_of(brief_path).lower()
    print(f'ブリーフ: {brief_path}')
    print(f'  出題履歴JSONの sha256 : {declared[:16]}…')
    print(f'  ブリーフ実物の sha256 : {actual[:16]}…')
    if actual != declared:
        print('[NG] sha256 が一致しない。'
              '＝ブリーフを反映していない／ブリーフが更新された／別教科のブリーフ。'
              '最新のブリーフを開いて反映し、正しい sha256 を入れ直すこと。')
        return 1

    print('[OK] 設計ブリーフ（中間本番の分析）を反映した模試であることを確認。')
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.stdout.reconfigure(encoding='utf-8')
    jp = sys.argv[1]
    bp = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('DESIGN_BRIEF', '')
    sys.exit(check(jp, bp))
