---
name: workbook-image-process
description: ワークブック画像の回転・ページ数読み取り・リネームを一括処理する。「ワーク画像を処理して」「画像を回転してリネームして」と言ったときに使う。
---

# workbook-image-process スキル

## 概要
ワークブック（算数・理科・国語など）の見開き画像に対して：
1. EXIF補正による回転
2. ページ数の視覚読み取り
3. ファイル名にページ数を追加（`元ファイル名_p12-13.jpg`）
を一括処理する。

## 呼び出し方
```
/workbook-image-process local ~/path/to/folder
/workbook-image-process drive ファイル名1.jpg ファイル名2.jpg ... --dest ~/path/to/folder
```

---

## ステップ1：ファイル取得

### ローカルの場合
指定フォルダ内のJPEGファイル一覧を確認する。

### Driveの場合
1. 各ファイル名で `mcp__claude_ai_Google_Drive__search_files` を呼んでファイルIDを取得
2. `mcp__claude_ai_Google_Drive__download_file_content` でbase64データを取得
3. 以下のPythonコマンドで --dest フォルダに保存する

```bash
python3 -c "
import base64, sys
b64 = sys.argv[1]
out = sys.argv[2]
open(out, 'wb').write(base64.b64decode(b64))
" "<base64文字列>" "<保存先パス>"
```

---

## ステップ2：回転

```bash
python3 ~/dotfiles/claude/scripts/workbook_rotate.py <フォルダパス>
```

**重要ルール**:
- このスクリプトがEXIFタグを読んで回転し、orientationタグを除去して保存する
- EXIF除去後はReadツールとユーザーのビューアーが同じピクセルを見ている → 視覚確認が有効

**資料タイプ別の正解レイアウト**（スクリプト実行後にReadツールで確認する）:
- 見開きワークブック（算数・理科・国語）→ **横長** + 首を傾けずに読める
- 縦書きテスト（漢字テストなど）→ **横長** + ①⑩が右から左に横並び + 各列縦書き
- 横書き1枚もの → **縦長** + 横書きで読める

「文字が読めるかどうか」だけでなく「そのドキュメントの正しいレイアウトになっているか」を確認する。

**⚠️ 向きが違う場合の修正**:
縦長になっているべき資料が縦長でない、または横長になっているべき資料が縦長のままの場合はCW 90°追加回転。
```python
from PIL import Image
img = Image.open(path)
img = img.rotate(-90, expand=True)  # CW 90°
img.save(path, format='JPEG', quality=95)
```

---

## ステップ3：ページ数読み取り＆リネーム

回転後の各ファイルを Read ツールで表示し、**画像下端の左右コーナー**からページ数を読み取る。

### 読み取りルール
- 両コーナー読み取れた → そのまま使用（例: p12-13）
- 片側が見切れ → 見えている方から連番で推測（両開きなので連続している）
- **完全に読み取れない場合 → 処理を中断してユーザーに報告し、入力を待つ**

### リネーム
```bash
mv 元ファイル名.jpg 元ファイル名_p12-13.jpg
```

---

## ステップ4：Drive への書き戻し（Driveモードのみ）

元ファイルが保存されていたDriveフォルダのパスをユーザーに確認し、rcloneでアップロードする。

```bash
rclone copy <ローカルフォルダ>/ gdrive:<Driveフォルダパス>/ --include "*.jpg"
```

**注意**: Drive上の元ファイルの削除はユーザーが手動で行う（削除MCPツールなし）

---

## ステップ5：完了報告

処理結果を表形式で表示する：

```
処理完了: XX枚

ファイル名                          回転      ページ
20260517_105035_p4-5.jpg           CW(6)     p4-5
20260517_105042_p6-7.jpg           CW(6)     p6-7
20260517_105049_pXX-XX.jpg         CW(6)     要確認（入力待ち）
```
