# workbook-image-process スキル 要件定義

作成日: 2026-05-29

## 概要

ワークブック画像の回転・ページ数読み取り・リネームを一括処理するスキル。
ローカルフォルダおよびGoogle Driveのファイルを対象とする。

## 呼び出し方

```
# ローカル
/workbook-image-process local ~/path/to/folder

# Google Drive（ファイル名指定）
/workbook-image-process drive ファイル名1.jpg ファイル名2.jpg ... --dest ~/path/to/folder
```

## 処理フロー

### ① ファイル取得

- **ローカル**: 指定フォルダの画像を一覧取得
- **Drive**: 指定ファイル名でDrive検索 → ダウンロード → 指定ローカルフォルダに保存

### ② 回転（EXIF補正）

EXIFタグを読み取り、機械的に回転する。視覚判断は行わない。

```python
rotation_map = {1: 0, 3: 180, 6: -90, 8: 90}

def rotate_by_exif(path):
    img = Image.open(path)
    orientation = img.getexif().get(274, 1)
    degrees = rotation_map.get(orientation, 0)
    if degrees != 0:
        img = img.rotate(degrees, expand=True)
    exif = img.getexif()
    if 274 in exif:
        del exif[274]  # 二重補正防止
    img.save(path, format='JPEG', quality=95, exif=exif.tobytes())
```

**重要ルール**:
- Readツールは EXIF 補正済みで表示するため、視覚での方向判断は不可
- EXIF タグの値のみを根拠に回転する
- 保存時に orientation タグを除去する

### ③ ページ数読み取り＆リネーム

- 画像底部の左右コーナーに記載されたページ数を読み取る
- 両開き見開き: 左ページ番号 + 右ページ番号（例: p12-13）
- 片側が見切れている場合: 見えている側から連番で推測
- **完全に読み取れない場合**: ユーザーに報告してページ数の入力を待つ

リネーム形式: `{元ファイル名}_p{左}-{右}.jpg`

### ④ Drive への書き戻し（Drive処理時のみ）

- 処理済みファイルを rclone でアップロード
- 元ファイルの削除はユーザーが手動で行う

**技術的制約**:
- Drive MCP `create_file` は大容量ファイル（約4.8MB超）で失敗するため rclone を使用
- Drive に上書き・削除 MCP ツールは存在しないため、同名ファイルが新規追加される

### ⑤ 完了報告

```
処理完了: 11枚

ファイル名                          回転      ページ
20260517_105035_p4-5.jpg           CW(6)     p4-5
20260517_105042_p6-7.jpg           CW(6)     p6-7
...
20260517_105138_pXX-XX.jpg         CW(6)     要確認（入力待ち）
```

## 技術スタック

- Python / Pillow（画像処理・EXIF操作）
- Google Drive MCP（ファイル検索・ダウンロード）
- rclone（Drive へのアップロード）
