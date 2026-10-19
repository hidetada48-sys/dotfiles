# -*- coding: utf-8 -*-
"""画面下の確認の枠（デスクトップ版の作業の終わりの枠）に、質問とボタンを出させない見張り（2026-10-20 専務承認）

- 対象＝mcp__ccd_turn__wrap_up（作業の終わりに要約を出す操作）
- 質問（ask）・ボタン（actions）・待ち（blocked）があれば消し、要約（recap）だけにして通す
  ＝枠は出ず、専務の画面には precheck で測った回答の文だけが出る
- 理由：質問を枠に渡すと、アプリの決まりで回答の文が画面に出なくなる（10/20 に原因の説明とレポートのリンクが届かなかった）
- 止めずに書き換えるだけ＝専務の画面に警告は出ない。消したときは私（Claude）にだけ一言知らせる
- 公式の説明：PreToolUse の hookSpecificOutput.updatedInput は道具の引数を丸ごと置き換える（code.claude.com/docs/en/hooks）
"""
import json
import sys

DROP = ("ask", "actions", "blocked")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0                                   # 読めなければ何もしない（作業は止めない）
    inp = data.get("tool_input") or {}
    try:                                           # 動いた記録（見張りが効いているかを確かめるため）
        import datetime, os
        p = os.path.expanduser("~/.claude/state/wrapup-noask.log")
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')}\t{'消した' if any(k in inp for k in DROP) else '要約だけ'}\n")
    except Exception:
        pass
    if not any(k in inp for k in DROP):
        return 0                                   # 要約だけ＝そのまま通す
    new = {k: v for k, v in inp.items() if k not in DROP}
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "updatedInput": new,
        "additionalContext": "【見張り】画面下の枠の質問・ボタンを消しました。伺いは precheck で測った回答の文に書いて出すこと。",
    }}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
