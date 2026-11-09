# 日報アプリの「原料在庫の知らせ」のファイルが書き換わるのを待ち、書き換わるたびに中身の1行を出す（2026-11-10 専務承認）
# 操作盤（register.tsx の watchGenryo）が起こし、私に原料在庫の計算を1回頼んだら止める＝1日1回
# 操作盤（Claude Code の拡張）はネットワーク上のファイルを読めない決まりなので、サーバーを見るのはこのプログラムが受け持つ
# 書き換わりは Windows の合図（FileSystemWatcher）で受ける＝繰り返し見に行かない
param(
  [Parameter(Mandatory = $true)][string]$Dir,    # 知らせのフォルダ（共用フォルダの 日報アプリ\知らせ）
  [Parameter(Mandatory = $true)][string]$Name    # 知らせのファイル名（原料在庫.txt）
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8

# サーバーに届かない日（社外・停電など）は待たずに終わる＝次の朝の定例業務 No.28 で計算される
if (-not (Test-Path -LiteralPath $Dir)) {
  [Console]::Out.WriteLine('NOREACH')
  exit 0
}

# ファイル名で絞らずにフォルダ全体を受ける（名前で絞ると、日報アプリの「別名で書いて差し替え」の合図を受け取れなかった＝11/10 試験）
$w = New-Object IO.FileSystemWatcher $Dir
$w.NotifyFilter = [IO.NotifyFilters]'FileName, LastWrite, Size'
[Console]::Out.WriteLine('READY')
[Console]::Out.Flush()

while ($true) {
  # 10分ごとに一度だけ、サーバーにまだ届くかを確かめる（届かなくなったら終わる）
  $r = $w.WaitForChanged([IO.WatcherChangeTypes]::All, 600000)
  if ($r.TimedOut) {
    if (-not (Test-Path -LiteralPath $Dir)) { exit 0 }
    continue
  }
  if ($r.ChangeType -eq [IO.WatcherChangeTypes]::Deleted) { continue }
  if ($r.Name -ne $Name) { continue }                              # 知らせのファイル以外（書き込み中の別名など）は見送る
  # 日報アプリは別名で書いてから差し替えるので、差し替えが済むのを少し待ってから読む
  Start-Sleep -Milliseconds 300
  try {
    $t = [IO.File]::ReadAllText((Join-Path $Dir $Name), [Text.Encoding]::UTF8).Trim()
  } catch {
    continue
  }
  if ($t -ne '') {
    [Console]::Out.WriteLine("NOTICE`t$t")
    [Console]::Out.Flush()
  }
}
