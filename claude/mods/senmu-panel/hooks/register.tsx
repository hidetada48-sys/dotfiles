// 専務の操作盤
// ・入力欄の上：〔保存3点〕〔横で質問〕〔控え帳〕（いつも出す）と、起動時の〔最新を取り込む〕
// ・右側の窓（/panel で開く）：〔未決事項〕〔横で質問〕〔控え帳〕を切り替えて表示
import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { NoteItem, Pending, Tab } from '../types'

const PLUGIN = 'senmu-panel'
const PANE = 'senmu-panel'
const TITLE = '専務の操作盤'

// 画面の表示に使う値（会話の間だけ。再読み込みでも消えない）
const tab = atom({ plugin: 'senmu-panel', key: 'tab' } as const, 'pending' as Tab)
const isPullOffered = atom({ plugin: 'senmu-panel', key: 'isPullOffered' } as const, false)
const isPullAsked = atom({ plugin: 'senmu-panel', key: 'isPullAsked' } as const, false)
const pullStatus = atom({ plugin: 'senmu-panel', key: 'pullStatus' } as const, '')
const pending = atom({ plugin: 'senmu-panel', key: 'pending' } as const, [] as Pending[])
const notes = atom({ plugin: 'senmu-panel', key: 'notes' } as const, [] as NoteItem[])
const sideAnswer = atom({ plugin: 'senmu-panel', key: 'sideAnswer' } as const, '')
const isSideBusy = atom({ plugin: 'senmu-panel', key: 'isSideBusy' } as const, false)

// PCをまたいで残す値の置き場（そのPCの中）
const STORE_PENDING = 'pending'
const STORE_VIOLATIONS_SEEN = 'violationsSeen'

// 伺いで終わった返答かどうか（最後の行の終わり方で見る）
const ASK_END = /(でしょうか|ませんか|ますか|しますか|ください|か)[。？?！!）)]*$/

type Dollar = EngineInterface

// ホームのフォルダ（Linux は HOME、Windows は USERPROFILE）
async function home($: Dollar): Promise<string> {
  const h = (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE')) ?? ''
  return h.replace(/\\/g, '/').replace(/\/$/, '')
}

// 控え帳のファイル（両方のPCが読む設定の保管場所 dotfiles の中）
async function notesFile($: Dollar): Promise<string> {
  return `${await home($)}/dotfiles/claude/hikaecho/hikaecho.jsonl`
}

// このPCの名前（控え帳に、どちらのPCで起きたかを残す）
async function pcName($: Dollar): Promise<string> {
  const env = (await $.env.get('COMPUTERNAME')) ?? (await $.env.get('HOSTNAME'))
  if (env) return env
  try {
    const r = await $.process.run(['hostname'])
    return r.stdout.trim() || 'pc'
  } catch {
    return 'pc'
  }
}

// 今の日時を「2026-10-08 19:30」の形で
async function stamp($: Dollar): Promise<string> {
  const d = new Date(await $.clock.now())
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

// 控え帳を読む（ファイルが無ければ空）
async function loadNotes($: Dollar): Promise<NoteItem[]> {
  const path = await notesFile($)
  if (!(await $.fs.exists(path))) return []
  const text = await $.fs.read(path)
  const list: NoteItem[] = []
  for (const line of text.split('\n')) {
    if (line.trim() === '') continue
    try {
      list.push(JSON.parse(line) as NoteItem)
    } catch {
      // 壊れた行は飛ばす
    }
  }
  return list
}

// 控え帳を書き戻し、画面の値もそろえる
async function saveNotes($: Dollar, list: NoteItem[]): Promise<void> {
  const body = list.map(n => JSON.stringify(n)).join('\n')
  await $.fs.write(await notesFile($), body === '' ? '' : body + '\n')
  await update($, notes, () => list)
}

// 控え帳に1件足す
async function addNote($: Dollar, source: 'senmu' | 'auto', text: string, at?: string): Promise<void> {
  const list = await loadNotes($)
  const when = at ?? (await stamp($))
  list.push({
    id: `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`,
    at: when,
    pc: await pcName($),
    source,
    text,
    status: 'open',
  })
  await saveNotes($, list)
}

// 返答の決まり違反の記録（html-gate_violations.log）から、新しい分を控え帳に自動で載せる
async function importViolations($: Dollar): Promise<void> {
  const path = `${await home($)}/.claude/state/html-gate_violations.log`
  if (!(await $.fs.exists(path))) return
  const lines = (await $.fs.read(path)).split('\n').filter(l => l.trim() !== '')
  const seen = (await $.store.get(STORE_VIOLATIONS_SEEN)) as number | undefined
  // 初めて動いたときは、これまでの分は載せずに数だけ覚える
  if (seen === undefined || seen > lines.length) {
    await $.store.set(STORE_VIOLATIONS_SEEN, lines.length)
    return
  }
  for (const line of lines.slice(seen)) {
    const [at, reason, excerpt] = line.split('\t')
    const head = (excerpt ?? '').slice(0, 40)
    await addNote($, 'auto', `返答の決まり違反：${reason ?? ''}${head ? `（返答の書き出し「${head}」）` : ''}`, at)
  }
  await $.store.set(STORE_VIOLATIONS_SEEN, lines.length)
}

// 未決事項を、画面とそのPCの保存場所の両方に書く
// 未決事項のファイル（そのPCの中）。決まった伺いは私がこのファイルから外す
async function pendingFile($: Dollar): Promise<string> {
  return `${await home($)}/.claude/state/senmu-pending.json`
}

// 未決事項をファイルから読む。ファイルが無ければ、前に操作盤の中に保存した分を使う
async function loadPending($: Dollar): Promise<Pending[]> {
  const path = await pendingFile($)
  if (await $.fs.exists(path)) {
    try {
      return JSON.parse(await $.fs.read(path)) as Pending[]
    } catch {
      return []
    }
  }
  return ((await $.store.get(STORE_PENDING)) as Pending[] | undefined) ?? []
}

// 未決事項を、画面とファイルの両方に書く（書く前にファイルを読み直し、私が外した分を生かす）
async function setPending($: Dollar, fn: (list: Pending[]) => Pending[]): Promise<void> {
  const next = fn(await loadPending($))
  await update($, pending, () => next)
  await $.fs.write(await pendingFile($), JSON.stringify(next, null, 1) + '\n')
}

// 専務が打ったのと同じ形で私に依頼を送る
async function send($: Dollar, text: string): Promise<void> {
  await $.prompt.submit({ text, asUser: true })
}

// ホームの下にある Git の保管場所（リポジトリ）を探す
async function findRepos($: Dollar): Promise<string[]> {
  const h = await home($)
  const repos: string[] = []
  for (const entry of await $.fs.list(h)) {
    if (entry.kind !== 'dir' || entry.name.startsWith('.')) continue
    if (await $.fs.exists(`${h}/${entry.name}/.git`)) repos.push(`${h}/${entry.name}`)
  }
  return repos
}

// 全リポジトリにリモートの最新を取り込む。保存していない変更がある所は取り込まず、私に伺わせる
async function pullAll($: Dollar): Promise<void> {
  await update($, pullStatus, () => '取り込み中…')
  const done: string[] = []
  const dirty: string[] = []
  const failed: string[] = []
  for (const repo of await findRepos($)) {
    const name = repo.split('/').pop() ?? repo
    try {
      const st = await $.process.run(['git', '-C', repo, 'status', '--porcelain'])
      if (st.stdout.trim() !== '') {
        dirty.push(name)
        continue
      }
      const r = await $.process.run(['git', '-C', repo, 'pull', '--ff-only'], { timeoutMs: 120000 })
      if (r.exitCode === 0) done.push(name)
      else failed.push(`${name}（${(r.stderr || r.stdout).trim().split('\n')[0] ?? ''}）`)
    } catch (err) {
      failed.push(`${name}（${String(err).slice(0, 60)}）`)
    }
  }
  const summary =
    `取り込み済み ${done.length}件` +
    (dirty.length ? `／保存していない変更あり ${dirty.length}件` : '') +
    (failed.length ? `／失敗 ${failed.length}件` : '')
  await update($, pullStatus, () => summary)
  await update($, isPullOffered, () => false)
  $.ui.toast(`最新の取り込み：${summary}`)
  if (dirty.length || failed.length) {
    const lines = [
      '起動時の〔最新を取り込む〕の結果です。',
      `取り込み済み：${done.join('、') || 'なし'}`,
    ]
    if (dirty.length) lines.push(`保存していない変更があり取り込まなかった：${dirty.join('、')}。変更の中身を見せて、破棄するか残すかを伺って。`)
    if (failed.length) lines.push(`取り込めなかった：${failed.join('、')}。原因を調べて報告して。`)
    await $.prompt.submit({ text: lines.join('\n') })
  }
}

// 保存3点：コミット・プッシュ・記憶を頼み、控え帳の残りの件数を知らせる
async function saveAll($: Dollar): Promise<void> {
  const left = (await loadNotes($)).filter(n => n.status === 'open').length
  $.ui.toast(`控え帳の残り：${left}件`)
  await send(
    $,
    `今日の作業をコミット・プッシュ・記憶まで保存して（作業したリポジトリと dotfiles の両方を確認）。控え帳の残りは ${left}件と最後に知らせて。`,
  )
}

// 入力欄の上のボタンから、右側の窓を指定の切り替えで開き、すぐ文字を打てるようにする（私の作業は止めない）
async function openTab($: Dollar, t: Tab): Promise<void> {
  await update($, tab, () => t)
  await $.ui.open({ id: PANE, title: TITLE, focus: true })
}

export const register: Register = on => {
  // 会話の開始：/panel を用意し、起動時の〔最新を取り込む〕を出す
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'panel', description: '専務の操作盤を開く' })
    try {
      const saved = await loadPending($)
      await update($, pending, () => saved)
    } catch {
      // 読めなくても会話は続ける
    }
    // 〔最新を取り込む〕は会話の最初（まだ一度もやり取りしていないとき）だけ出す。
    // 操作盤を直して読み込み直したときは、出ていても下げる
    const isFirst = (await $.session.turns()) === 0 && !(await read($, isPullAsked))
    await update($, isPullAsked, () => true)
    await update($, isPullOffered, () => isFirst)
    try {
      await importViolations($)
      const list = await loadNotes($)
      await update($, notes, () => list)
    } catch {
      // 控え帳が読めなくても会話は続ける
    }
    return next(e)
  })

  // /panel：右側の窓を開く
  on('command.run', { command: 'panel' }, async $ => {
    await $.ui.open({ id: PANE, title: TITLE })
    return { text: '専務の操作盤を開きました。' }
  })

  // 専務が何か送ったら、〔最新を取り込む〕は下げる。決まり違反の新しい記録も控え帳に載せる
  on('prompt.submit', async ($, e, next) => {
    if ((await read($, pullStatus)) !== '取り込み中…') await update($, isPullOffered, () => false)
    try {
      await importViolations($)
    } catch {
      // 読めなくても依頼は止めない
    }
    return next(e)
  }).catch(($, e, next) => next(e)) // 失敗しても専務の依頼は必ず通す

  // 返答の終わり：伺いで終わっていれば未決事項に載せる
  on('turn.complete', async ($, e, next) => {
    try {
      const list = await loadNotes($)
      await update($, notes, () => list)
      const pend = await loadPending($)
      await update($, pending, () => pend)
    } catch {
      // 読めなくても返答は止めない
    }
    if (e.agentId === undefined && e.reason === 'answer') {
      const lines = e.answer.split('\n').map(l => l.replace(/[*_`#>]/g, '').trim()).filter(l => l !== '')
      const last = lines[lines.length - 1] ?? ''
      // 控え帳（専務が書き留めた、業務と関係のない出来事）についての伺いは、未決事項に入れない
      const isAboutNotes = /控え帳|控帳|まとめて対処/.test(e.answer)
      if (ASK_END.test(last) && !isAboutNotes) {
        const at = await stamp($)
        await setPending($, list => [...list, { id: `${Date.now().toString(36)}`, at, text: last.slice(0, 200) }].slice(-50))
      }
    }
    return next(e)
  })

  // 入力欄の上の帯
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey) return next(e)
    const offered = await read($, isPullOffered)
    const status = await read($, pullStatus)
    const { Box, Button, Text } = $.ui.resolve(e)

    return (
      <Box flexDirection="column">
        <Box gap={1}>
          <Button key="save" label="保存3点" onPress={() => saveAll($)} />
          <Button key="open-ask" label="横で質問" onPress={() => openTab($, 'ask')} />
          <Button key="open-notes" label="控え帳" onPress={() => openTab($, 'notes')} />
        </Box>
        {offered && (
          <Box gap={1}>
            <Button key="pull" label="最新を取り込む" variant="primary" onPress={() => pullAll($)} />
            <Button key="pull-skip" label="今回はしない" onPress={() => update($, isPullOffered, () => false)} />
            {status !== '' && <Text dimColor>{status}</Text>}
          </Box>
        )}
      </Box>
    )
  })

  // 右側の窓
  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const els = $.ui.resolve(e)
    const { Box, Button, Text } = els
    // 文字を打つ欄（Input）はスマホと VS Code の画面には無い
    const Input = 'Input' in els ? els.Input : undefined
    const current = await read($, tab)
    const pend = await read($, pending)
    const noteList = await read($, notes)
    const open = noteList.filter(n => n.status === 'open')

    // 切り替えのボタン
    const tabs: { key: Tab; label: string }[] = [
      { key: 'pending', label: `未決事項 ${pend.length}` },
      { key: 'ask', label: '横で質問' },
      { key: 'notes', label: `控え帳 ${open.length}` },
    ]
    const header = (
      <Box gap={1} flexWrap="wrap">
        {tabs.map(t => (
          <Button
            key={`tab-${t.key}`}
            label={t.label}
            variant={t.key === current ? 'primary' : 'secondary'}
            onPress={() => update($, tab, () => t.key)}
          />
        ))}
      </Box>
    )

    let body
    if (current === 'pending') {
      // 〔未決事項〕：私の伺いの一覧（決まった伺いは私がファイルから外し、一覧から消える）
      body = (
        <Box flexDirection="column">
          {pend.length === 0 && <Text dimColor>未決事項はありません。</Text>}
          {pend.map(p => (
            <Box key={`p-${p.id}`} gap={1}>
              <Text>
                {p.at} {p.text}
              </Text>
            </Box>
          ))}
        </Box>
      )
    } else if (current === 'ask') {
      // 〔横で質問〕：作業を止めずに、今の会話の中身だけで答えさせる
      const answer = await read($, sideAnswer)
      const busy = await read($, isSideBusy)
      body = (
        <Box flexDirection="column" gap={1}>
          {Input ? (
            <Input
              key="side-q"
              autoFocus
              placeholder="例：今どこまで進んだか"
              submitLabel="質問する"
              onSubmit={async (q: string) => {
                if (q.trim() === '') return
                await update($, isSideBusy, () => true)
                await update($, sideAnswer, () => '')
                const r = await $.model.fork({
                  prompt: `（専務が作業の横から質問しています。ファイルの読み書きや命令の実行はせず、今の会話の内容だけで、日本語で簡潔に答えてください）\n${q}`,
                })
                await update($, sideAnswer, () => (r.isAnswered ? r.text : `答えられませんでした（${r.reason}）`))
                await update($, isSideBusy, () => false)
              }}
            />
          ) : (
            <Text dimColor>この画面では文字を打てません。端末かデスクトップの画面で開いてください。</Text>
          )}
          {busy && <Text dimColor>考えています…</Text>}
          {answer !== '' && <Text>{answer}</Text>}
        </Box>
      )
    } else {
      // 〔控え帳〕：業務と関係のない出来事の一覧、〔控え帳に書く〕と〔まとめて対処〕（対処が済んだ件は私がファイルで済にし、一覧から消える）
      body = (
        <Box flexDirection="column" gap={1}>
          {Input ? (
            <Input
              key="note-new"
              autoFocus
              placeholder="例：返答が長すぎた"
              submitLabel="控え帳に書く"
              onSubmit={async (text: string) => {
                if (text.trim() === '') return
                await addNote($, 'senmu', text.trim())
                $.ui.toast('控え帳に書きました')
              }}
            />
          ) : (
            <Text dimColor>この画面では文字を打てません。端末かデスクトップの画面で開いてください。</Text>
          )}
          {open.length === 0 && <Text dimColor>控え帳の残りはありません。</Text>}
          {open.map(n => (
            <Text key={`n-${n.id}`}>
              {n.at} {n.text}
            </Text>
          ))}
          {open.length > 0 && (
            <Button
              key="note-all"
              label={`まとめて対処（${open.length}件）`}
              variant="primary"
              onPress={async () => {
                const path = await notesFile($)
                const list = open.map(n => `・[${n.id}] ${n.at} ${n.text}`).join('\n')
                await send(
                  $,
                  `控え帳（${path}）の未対応 ${open.length}件をまとめて対処して。1件ずつ原因と直し方を出し、直した件は status を done にして doneAt と how（直し方）を書いて。\n${list}`,
                )
              }}
            />
          )}
        </Box>
      )
    }

    return (
      <Box flexDirection="column" gap={1}>
        {header}
        {body}
      </Box>
    )
  })
}
