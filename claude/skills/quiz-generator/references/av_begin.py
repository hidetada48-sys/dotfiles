#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# answer-validator の「開始トークン」発行（2026-08-18 新設・再発防止）。
#
# なぜ要るか（2026-08-18 の失敗）：
#   av_report/av_stamp はスクリプトなので、answer-validator スキルを起動せずに直接叩けば、
#   スキルの解き直し(2A)・転記突合(2B)・知識検証(2C)を通さないまま「検証済み」を偽装できた
#   （数学中間模試で実際に発生：スキルを起動せず av_report を直叩きしてレシートを作った）。
#   そこで answer-validator スキルの「ステップ0」でこの開始トークンを必ず発行させ、
#   av_report がトークン（対象HTMLの sha 一致・新しさ）を要求する。
#   ＝スキルのステップ0を通っていなければ av_report が受理せず、レシートもスタンプも作れない。
#
# 使い方（answer-validator SKILL.md ステップ0で必ず実行する）:
#   python3 av_begin.py <html>
import sys, os, json, hashlib, datetime, secrets


def main():
    if len(sys.argv) < 2:
        print("使い方: av_begin.py <html>")
        return 2
    html = sys.argv[1]
    if not os.path.isfile(html):
        print(f"[NG] HTMLが無い: {html}")
        return 2
    sha = hashlib.sha256(open(html, "rb").read()).hexdigest()
    tok = {
        "html_sha256": sha,
        "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "nonce": secrets.token_hex(8),
    }
    open(html + ".avbegin.json", "w", encoding="utf-8").write(
        json.dumps(tok, ensure_ascii=False, indent=2))
    print(f"[OK] answer-validator 開始トークンを発行: {os.path.basename(html)}.avbegin.json")
    print(f"      sha256={sha[:16]}…  以後 av_report はこのトークンが無い/不一致だと受理しない。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
