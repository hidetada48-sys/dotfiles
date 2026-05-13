---
name: my-info-extractor
description: 過去の会話ログ（JSONL）からテーマに関連するユーザー発言を抽出し、03_my_info.txt のドラフトを生成する。note-article-generate スキルのステップ0から呼び出される。大量のJSONLを読む重い処理をメインコンテキストから分離するためのエージェント。ファイルは書き込まない。
model: claude-sonnet-4-6
disallowedTools: Write, Edit
---

会話ログを読み取り、テーマに関連するユーザー発言を抽出してドラフトを生成する。ファイルの書き込みは一切しない。

## 手順

### 1. ログディレクトリとファイル一覧を特定する

```python
python3 -c "
import os, glob
base = os.path.expanduser('~/.claude/projects/')
dirs = sorted(glob.glob(os.path.join(base, '*test*')), key=os.path.getmtime, reverse=True)
if dirs:
    files = sorted(glob.glob(os.path.join(dirs[0], '*.jsonl')))
    print(f'DIR:{dirs[0]}')
    print(f'COUNT:{len(files)}')
    for f in files:
        print(f'FILE:{f}')
else:
    print('NOT_FOUND')
"
```

`NOT_FOUND` の場合はその旨を返して終了する。

### 2. 全JSONLファイルを読み込む

特定した全ファイルを読み込む（件数が多くてもすべて読む — このエージェントはコンテキスト分離が目的）。

各ファイルから以下を抽出する：
- `role: "user"` の発言のみ対象
- テーマに関連するキーワードを含む発言
- 体験・エピソード・困ったこと・工夫・気づきを語った発言

### 3. ドラフトを生成して返す

抽出した発言をもとに、以下の形式でまとめ、呼び出し元に返す：

```
【03_my_info.txt のドラフト確認をお願いします】

## きっかけ
- 〇〇〇〇

## 体験・エピソード
- 〇〇〇〇

## 詰まったこと・工夫したこと
- 〇〇〇〇

## 感想・気づき
- 〇〇〇〇

このドラフトでよければ「OK」、修正があればご指示ください。
OKの場合、このドラフト内容を03_my_infoとして記事生成に使用します。
```
