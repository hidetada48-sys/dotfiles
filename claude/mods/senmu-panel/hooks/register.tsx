// 専務の操作盤
// ・入力欄の上：その日の最初の起動なら取り込みの結果の1行と、〔保存3点〕〔横で質問〕〔控え帳〕（いつも出す）
// ・右側の窓（/panel で開く）：〔未決事項〕〔横で質問〕〔控え帳〕を切り替えて表示
// ・1日1回、その日の最初の起動で、全リポジトリに最新を自動で取り込む
//   ★2026-10-13 専務指摘：〔最新を取り込む〕ボタンは最初の依頼を送ったあと（作業中）にしか出ず、
//     最初に取り込めなかった。起動の処理は画面を開いた時点で動くので、ボタンをやめて起動時に自動で取り込む
//     （「1日1回最初の起動時だけでよい」＝専務指示）。業務リポジトリの1日1回の取り込み（session-git-pull.sh）は
//     同時に取り込むとぶつかるため、設定から外した
import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { NoteItem, Pending, Tab } from '../types'

const PLUGIN = 'senmu-panel'
const PANE = 'senmu-panel'
const TITLE = '専務の操作盤'

// 画面の表示に使う値（会話の間だけ。再読み込みでも消えない）
const tab = atom({ plugin: 'senmu-panel', key: 'tab' } as const, 'pending' as Tab)
// 起動時の取り込みの結果（全リポジトリ分）。私が最初の返答で報告する。渡したら空にする
const pullNote = atom({ plugin: 'senmu-panel', key: 'pullNote' } as const, '')
// 起動時の取り込みの結果を、専務の画面（入力欄の上の帯）に出す1行。その会話の間ずっと出す
// ★2026-10-16 専務指摘「取り込みの結果を出るようにしたのに出ていない」：結果は最初の依頼に添えて私に届くだけで、
//   起動しただけでは画面に出なかった（右下の知らせは件数だけで、すぐ消える）。起動した時点で帯に出す
const pullShown = atom({ plugin: 'senmu-panel', key: 'pullShown' } as const, '')
const pending = atom({ plugin: 'senmu-panel', key: 'pending' } as const, [] as Pending[])
const notes = atom({ plugin: 'senmu-panel', key: 'notes' } as const, [] as NoteItem[])
const sideAnswer = atom({ plugin: 'senmu-panel', key: 'sideAnswer' } as const, '')
const isSideBusy = atom({ plugin: 'senmu-panel', key: 'isSideBusy' } as const, false)
// 控え帳の入力欄の番号。書くたびに1つ増やして新しい欄に替え、書いた文を消す（2026-10-13 専務指摘「書いたものが消えない」）
const noteInputNo = atom({ plugin: 'senmu-panel', key: 'noteInputNo' } as const, 0)

// PCをまたいで残す値の置き場（そのPCの中）
const STORE_PENDING = 'pending'

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

// ※控え帳は専務が書き留める物（2026-10-08 決定）。私の決まり違反は別の記録（html-gate_violations.log）に残るので、
//   控え帳へは写さない（2026-10-12 専務承認で写す機能を外した）

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

// 今日の日付を「2026-10-13」の形で（そのPCの時刻）
async function today($: Dollar): Promise<string> {
  return (await stamp($)).slice(0, 10)
}

// その日の最初の起動だけ取り込む。取り込んだ日と結果は、そのPCの中のファイルに残す
//   senmu-pull-day.txt＝最後に取り込んだ日／senmu-pull-result.txt＝取り込んだ時刻と結果（時刻の確かめ用）
async function pullOncePerDay($: Dollar): Promise<void> {
  const h = await home($)
  const dayFile = `${h}/.claude/state/senmu-pull-day.txt`
  const day = await today($)
  if ((await $.fs.exists(dayFile)) && (await $.fs.read(dayFile)).trim() === day) return
  // 成否によらず今日は済とする（失敗しても毎回の起動でやり直さない）
  await $.fs.write(dayFile, day + '\n')
  const startedAt = await stamp($)
  const summary = await pullAll($)
  await $.fs.write(`${h}/.claude/state/senmu-pull-result.txt`, `${startedAt} 開始／${await stamp($)} 終了：${summary}\n`)
}

// 取り込みの途中かどうか。会話の始まり（session.start）と起動時の設定のフック（classic.SessionStart）の
// どちらが先に来ても、取り込みは1回だけ動かし、もう一方は終わるのを待つ
let pullRunning: Promise<void> | null = null
async function pullFirst($: Dollar): Promise<void> {
  if (!pullRunning) {
    pullRunning = (async () => {
      // 取り込みは会話の始まり（まだ一度もやり取りしていないとき）だけ。操作盤を直して読み込み直したときはしない
      if ((await $.session.turns()) !== 0) return
      try {
        await pullOncePerDay($)
      } catch (err) {
        $.ui.toast(`最新の取り込みに失敗：${String(err).slice(0, 60)}`)
      }
    })().finally(() => {
      pullRunning = null
    })
  }
  return pullRunning
}

// 全リポジトリにリモートの最新を取り込む。
// ★2026-10-13 専務指示「pullするのにいちいち細かいことを言われてこなかった」：保存していない変更があっても
//   一時退避して取り込み、戻す（--autostash）。専務には伺わない。戻すときに同じ行が重なったときだけ私に知らせる
// ★2026-10-15 専務指示「取り込みの結果を報告する運用に変えてほしい」「すべての結果を報告するんだよな」：
//   成功だけの日も含めて毎回、全リポジトリの結果をリポジトリ名ごとに、私の最初の返答の冒頭で報告する
async function pullAll($: Dollar): Promise<string> {
  const results: string[] = []   // リポジトリごとの結果（「mino-sakura-hq 更新3件を取り込み」など）
  const dirty: string[] = []
  const failed: string[] = []
  let doneCount = 0
  for (const repo of await findRepos($)) {
    const name = repo.split('/').pop() ?? repo
    try {
      // 取り込む前の位置を控え、あとで何件の更新を取り込んだかを数える
      const before = (await $.process.run(['git', '-C', repo, 'rev-parse', 'HEAD'], { timeoutMs: 10000 })).stdout.trim()
      // 通信がほぼ止まったら git 自身が約15秒で中断する（起動を長く待たせない）
      const r = await $.process.run(
        ['git', '-C', repo, '-c', 'http.lowSpeedLimit=1000', '-c', 'http.lowSpeedTime=15', 'pull', '--ff-only', '--autostash'],
        { timeoutMs: 60000 },
      )
      const said = `${r.stdout}\n${r.stderr}`
      const isDirty = /autostash/i.test(said) && /conflict/i.test(said)   // 退避した変更を戻すときに重なった
      if (r.exitCode !== 0 && !isDirty) {
        const why = (r.stderr || r.stdout).trim().split('\n')[0] ?? ''
        failed.push(name)
        results.push(`${name} 失敗（${why}）`)
        continue
      }
      doneCount++
      const n = before
        ? Number((await $.process.run(['git', '-C', repo, 'rev-list', '--count', `${before}..HEAD`], { timeoutMs: 10000 })).stdout.trim()) || 0
        : 0
      let line = n > 0 ? `${name} 更新${n}件を取り込み` : `${name} 変更なし`
      if (isDirty) {
        dirty.push(name)
        line += '（手元の未保存の変更を戻すときに同じ行が重なった）'
      }
      results.push(line)
    } catch (err) {
      failed.push(name)
      results.push(`${name} 失敗（${String(err).slice(0, 60)}）`)
    }
  }
  const summary =
    `取り込み済み ${doneCount}件` +
    (dirty.length ? `／変更が重なった ${dirty.length}件` : '') +
    (failed.length ? `／失敗 ${failed.length}件` : '')
  const shown = `最新の取り込み：${results.join('／') || '対象のリポジトリなし'}`
  $.ui.toast(shown)
  await update($, pullShown, () => shown)
  // 結果は専務の発言としてチャットに出さず、私への知らせ（システムの指示）で渡す。毎回渡す
  const lines = [
    '【操作盤：起動時の最新の取り込みの結果】',
    `最新の取り込み：${results.join('／') || '対象のリポジトリなし'}`,
    '上の1行を、最初の返答の冒頭にそのまま書いて専務に報告すること（成功だけの日も必ず書く）。',
  ]
  if (dirty.length) lines.push(`同じ行が重なったリポジトリ（${dirty.join('、')}）は、重なったファイル名も報告すること（破棄するか残すかは伺わない）。`)
  if (failed.length) lines.push(`失敗したリポジトリ（${failed.join('、')}）は、原因を調べて同じ返答で報告すること。`)
  await update($, pullNote, () => lines.join('\n'))
  return `${summary}：${results.join('／')}`
}

// 保存3点：コミット・プッシュ・記憶を頼む。控え帳の残りの件数は操作盤の画面だけに出す
// ★2026-10-13 専務指摘「お前がお前に言っているのか？俺に見える必要は全くない」：
//   ボタンの文は専務の発言としてチャットに出るため、Claude あての指示（両リポジトリの確認・控え帳の件数）を混ぜない。
//   両リポジトリの確認は作業の決まり（CLAUDE.md の保存3点セット）にある
// ★2026-10-13 専務指示「保存のたびに控え帳に対処するルールはいらない」：控え帳の残りの件数は出さない
async function saveAll($: Dollar): Promise<void> {
  await send($, '今日の作業をコミット・プッシュ・記憶まで保存して。')
}

// 入力欄の上のボタンから、右側の窓を指定の切り替えで開き、すぐ文字を打てるようにする（私の作業は止めない）
async function openTab($: Dollar, t: Tab): Promise<void> {
  await update($, tab, () => t)
  await $.ui.open({ id: PANE, title: TITLE, focus: true })
}

export const register: Register = on => {
  // 会話の開始：/panel を用意し、その日の最初の起動なら最新を取り込む
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'panel', description: '専務の操作盤を開く' })
    try {
      const saved = await loadPending($)
      await update($, pending, () => saved)
    } catch {
      // 読めなくても会話は続ける
    }
    await pullFirst($)
    try {
      const list = await loadNotes($)
      await update($, notes, () => list)
    } catch {
      // 控え帳が読めなくても会話は続ける
    }
    return next(e)
  })

  // 起動時の設定のフック（定例業務の表を作る teirei-alert.sh など）より先に取り込む
  // ★2026-10-17 専務承認（案1）：Linux で 10/16・10/17 と続けて、起動時に作った定例業務の表と、取り込む側の同じ表がぶつかり、
  //   mino-sakura-hq を取り込めなかった。操作盤のフックは設定のフックより上で動くので、ここで取り込みを済ませてから
  //   next(e)＝設定のフックへ渡す（取り込みが先・表づくりが後に固定する）
  on('classic.SessionStart', async ($, e, next) => {
    await pullFirst($)
    return next(e)
  })

  // /panel：右側の窓を開く
  on('command.run', { command: 'panel' }, async $ => {
    await $.ui.open({ id: PANE, title: TITLE })
    return { text: '専務の操作盤を開きました。' }
  })

  // 起動時の取り込みの結果を、最初の依頼に私あての知らせとして添える（専務の画面には出ない）
  on('prompt.submit', async ($, e, next) => {
    const note = await read($, pullNote)
    if (note === '') return next(e)
    await update($, pullNote, () => '')
    return next({ ...e, context: [...(e.context ?? []), note] })
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
    const { Box, Button, Text } = $.ui.resolve(e)
    const shown = await read($, pullShown)

    return (
      <Box flexDirection="column">
        {shown !== '' && <Text>{shown}</Text>}
        <Box gap={1}>
          <Button key="save" label="保存3点" onPress={() => saveAll($)} />
          <Button key="open-ask" label="横で質問" onPress={() => openTab($, 'ask')} />
          <Button key="open-notes" label="控え帳" onPress={() => openTab($, 'notes')} />
        </Box>
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
    const noteNo = await read($, noteInputNo)

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
            // 右側の窓の横幅いっぱいに広げる（欄は1行だけ＝Claude Code 本体の入力欄の仕様）
            <Box key="note-new-box" width="100%">
              <Input
                key={`note-new-${noteNo}`}
                autoFocus
                placeholder="例：返答が長すぎた"
                submitLabel="控え帳に書く"
                onSubmit={async (text: string) => {
                  if (text.trim() === '') return
                  await addNote($, 'senmu', text.trim())
                  await update($, noteInputNo, n => n + 1)   // 新しい欄に替えて、書いた文を消す
                  $.ui.toast('控え帳に書きました')
                }}
              />
            </Box>
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
