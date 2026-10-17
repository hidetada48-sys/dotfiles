// 未決事項の試験：伺いで終わった返答だけが未決事項に載る
import { expect, mock, test } from 'claude-code/testing'

const PANE = { plugin: 'senmu-panel', component: 'Pane', requestId: 'senmu-panel' } as const

// 試験の中の置き場の名前をそろえる（Windows は「/h/…」を「C:\h\…」に書き換えるため、どちらも「/h/…」として扱う）
const key = (p: string) => p.replace(/\\/g, '/').replace(/^[A-Za-z]:/, '')

test('伺いで終わると未決事項に載る', async ($, on) => {
  mock.clock(on)
  mock.store(on)
  on('turn.complete', ($, e) => ({ text: e.answer }))
  // ファイルの読み書きは、試験の中だけの入れ物で代わりに受ける
  mock.env(on, { HOME: '/h' })
  const files = new Map<string, string>()
  on('fs.exists', ($, e) => ({ value: files.has(key(e.path)) }))
  on('fs.read', ($, e) => ({ value: files.get(key(e.path)) ?? '' }))
  on('fs.write', ($, e) => {
    files.set(key(e.path), e.text)
    return { value: undefined }
  })
  await $.turn.complete({
    answer: '設計がまとまりました。\n\nこの設計で作ってよろしいでしょうか。',
    durationMs: 1,
    isAborted: false,
    turnId: 't1',
    reason: 'answer',
  })
  // 右側の窓の〔未決事項〕に1件と出る
  const pane = await $.ui.mount({ ...PANE, surface: 'terminal', props: {} as never })
  expect((await pane.find({ key: 'tab-pending' }))?.text).toBe('未決事項 1')
  await pane.unmount()

  // 私がファイルから伺いを外すと、次の返答の終わりに一覧から消える
  files.set('/h/.claude/state/senmu-pending.json', '[]\n')
  await $.turn.complete({ answer: '承知しました。', durationMs: 1, isAborted: false, turnId: 't3', reason: 'answer' })
  const pane2 = await $.ui.mount({ ...PANE, surface: 'terminal', props: {} as never })
  expect((await pane2.find({ key: 'tab-pending' }))?.text).toBe('未決事項 0')
  await pane2.unmount()
})

test('伺いでない返答は未決事項に載らない', async ($, on) => {
  mock.clock(on)
  mock.store(on)
  on('turn.complete', ($, e) => ({ text: e.answer }))
  // ファイルの読み書きは、試験の中だけの入れ物で代わりに受ける
  mock.env(on, { HOME: '/h' })
  const files = new Map<string, string>()
  on('fs.exists', ($, e) => ({ value: files.has(key(e.path)) }))
  on('fs.read', ($, e) => ({ value: files.get(key(e.path)) ?? '' }))
  on('fs.write', ($, e) => {
    files.set(key(e.path), e.text)
    return { value: undefined }
  })
  await $.turn.complete({
    answer: '9月は68回です。',
    durationMs: 1,
    isAborted: false,
    turnId: 't2',
    reason: 'answer',
  })
  // 未決事項は0件のまま
  const pane = await $.ui.mount({ ...PANE, surface: 'terminal', props: {} as never })
  expect((await pane.find({ key: 'tab-pending' }))?.text).toBe('未決事項 0')
  await pane.unmount()
})

test('入力欄の上に〔保存3点〕〔横で質問〕〔控え帳〕がいつも出る', async ($, on) => {
  mock.clock(on)
  mock.store(on)
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ plugin: 'senmu-panel', component: 'AbovePrompt', surface, props: { hasSurvey: false } as never })
    expect((await ui.find({ key: 'save' }))?.text).toBe('保存3点')
    expect((await ui.find({ key: 'open-ask' }))?.text).toBe('横で質問')
    expect((await ui.find({ key: 'open-notes' }))?.text).toBe('控え帳')
    await ui.unmount()
  }
})

test('控え帳についての伺いは未決事項に入れない', async ($, on) => {
  mock.clock(on)
  mock.store(on)
  on('turn.complete', ($, e) => ({ text: e.answer }))
  mock.env(on, { HOME: '/h' })
  const files = new Map<string, string>()
  on('fs.exists', ($, e) => ({ value: files.has(key(e.path)) }))
  on('fs.read', ($, e) => ({ value: files.get(key(e.path)) ?? '' }))
  on('fs.write', ($, e) => {
    files.set(key(e.path), e.text)
    return { value: undefined }
  })
  await $.turn.complete({
    answer: '控え帳のテストの2件を消します。\n\nよろしいでしょうか。',
    durationMs: 1,
    isAborted: false,
    turnId: 't4',
    reason: 'answer',
  })
  const pane = await $.ui.mount({ ...PANE, surface: 'terminal', props: {} as never })
  expect((await pane.find({ key: 'tab-pending' }))?.text).toBe('未決事項 0')
  await pane.unmount()
})


// 起動時の取り込みの試験で使う入れ物（ファイルと git の呼び出しを試験の中だけで受ける）
//   updates＝リポジトリごとに取り込む更新の件数／failed＝取り込みに失敗させるリポジトリ
function mockPull(
  on: Parameters<Parameters<typeof test>[1]>[1],
  opts: { updates?: Record<string, number>; failed?: string[] } = {},
) {
  mock.env(on, { HOME: '/h' })
  // 会話の開始・/panel の登録・やり取りの回数（まだ0回）を試験の中で受ける
  on('session.start', ($, e) => ({ cwd: e.cwd }))
  on('command.register', ($, e) => ({ value: { command: e.name } }))
  on('session.turns', () => ({ value: 0 }))
  on('ui.toast', () => ({ value: undefined }))
  const files = new Map<string, string>()
  const git: string[] = []
  on('fs.exists', ($, e) => ({ value: files.has(key(e.path)) || /\/(mino-sakura-hq|dotfiles)\/\.git$/.test(key(e.path)) }))
  on('fs.read', ($, e) => ({ value: files.get(key(e.path)) ?? '' }))
  on('fs.write', ($, e) => {
    files.set(key(e.path), e.text)
    return { value: undefined }
  })
  on('fs.list', () => ({
    value: [
      { name: 'mino-sakura-hq', kind: 'dir', size: 0, mtimeMs: 0 },
      { name: 'dotfiles', kind: 'dir', size: 0, mtimeMs: 0 },
      { name: '.claude', kind: 'dir', size: 0, mtimeMs: 0 },
    ] as never,
  }))
  on('process.run', ($, e) => {
    const repo = key(e.argv[2] ?? '').split('/').pop() ?? ''
    const ok = (stdout: string) => ({ value: { exitCode: 0, stdout, stderr: '' } as never })
    if (e.argv.includes('rev-parse')) return ok('abc123\n')
    if (e.argv.includes('rev-list')) return ok(`${opts.updates?.[repo] ?? 0}\n`)
    git.push(`${repo}:pull`)
    if (opts.failed?.includes(repo)) {
      return { value: { exitCode: 128, stdout: '', stderr: 'fatal: Cannot fast-forward to multiple branches.\n' } as never }
    }
    return ok('')
  })
  return { files, git }
}

test('その日の最初の起動で全リポジトリを取り込み、同じ日の2回目はしない', async ($, on) => {
  mock.clock(on)
  mock.store(on)
  const { files, git } = mockPull(on)
  await $.session.start({ cwd: '/h/mino-sakura-hq', surface: 'desktop', isInteractive: true })
  expect(git).toEqual(['mino-sakura-hq:pull', 'dotfiles:pull'])
  expect(files.get('/h/.claude/state/senmu-pull-result.txt')?.includes('取り込み済み 2件')).toBe(true)
  git.length = 0
  await $.session.start({ cwd: '/h/mino-sakura-hq', surface: 'desktop', isInteractive: true })
  expect(git.length).toBe(0)
})

test('成功だけの日も、全リポジトリの結果をリポジトリ名ごとに最初の依頼に添える', async ($, on) => {
  mock.clock(on)
  mock.store(on)
  mockPull(on, { updates: { 'mino-sakura-hq': 3 } })
  on('prompt.submit', ($, e) => ({ text: e.text, context: e.context }))
  await $.session.start({ cwd: '/h/mino-sakura-hq', surface: 'desktop', isInteractive: true })
  // 最初の依頼に、私あての知らせ（専務の画面には出ない）として添わる。2回目の依頼には添えない
  const r1 = await $.prompt.submit({ text: '定例業務' } as never)
  const note = (r1.context ?? []).join('\n')
  expect(note.includes('最新の取り込み：mino-sakura-hq 更新3件を取り込み／dotfiles 変更なし')).toBe(true)
  expect(note.includes('成功だけの日も必ず書く')).toBe(true)
  const r2 = await $.prompt.submit({ text: '次の依頼' } as never)
  expect((r2.context ?? []).length).toBe(0)
})

test('失敗したリポジトリは原因の文と、原因を調べる指示を添える', async ($, on) => {
  mock.clock(on)
  mock.store(on)
  mockPull(on, { failed: ['dotfiles'] })
  on('prompt.submit', ($, e) => ({ text: e.text, context: e.context }))
  await $.session.start({ cwd: '/h/mino-sakura-hq', surface: 'desktop', isInteractive: true })
  const r1 = await $.prompt.submit({ text: '定例業務' } as never)
  const note = (r1.context ?? []).join('\n')
  expect(note.includes('mino-sakura-hq 変更なし／dotfiles 失敗（fatal: Cannot fast-forward to multiple branches.）')).toBe(true)
  expect(note.includes('失敗したリポジトリ（dotfiles）は、原因を調べて')).toBe(true)
})

test('起動した時点で、取り込みの結果を入力欄の上の帯に出す', async ($, on) => {
  mock.clock(on)
  mock.store(on)
  mockPull(on, { updates: { 'mino-sakura-hq': 3 } })
  await $.session.start({ cwd: '/h/mino-sakura-hq', surface: 'desktop', isInteractive: true })
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ plugin: 'senmu-panel', component: 'AbovePrompt', surface, props: { hasSurvey: false } as never })
    expect((await ui.find({ type: 'Text', text: /^最新の取り込み：/ }))?.text).toBe('最新の取り込み：mino-sakura-hq 更新3件を取り込み／dotfiles 変更なし')
    expect((await ui.find({ key: 'save' }))?.text).toBe('保存3点')
    await ui.unmount()
  }
})

test('起動時の設定のフック（定例業務の表づくり）より先に取り込みを済ませる', async ($, on) => {
  mock.clock(on)
  mock.store(on)
  const { git } = mockPull(on, { updates: { 'mino-sakura-hq': 14 } })
  // 試験の中のこのフックが、操作盤より下で動く設定のフック（teirei-alert.sh）の代わり。動いた時点の取り込みを控える
  const seenBySettingsHook: string[] = []
  on('classic.SessionStart', ($, e) => {
    seenBySettingsHook.push(...git)
    return {}
  })
  await $.classic.SessionStart({ source: 'startup' } as never)
  expect(seenBySettingsHook).toEqual(['mino-sakura-hq:pull', 'dotfiles:pull'])
  // そのあとの会話の始まりでは、同じ日なので取り込み直さない
  git.length = 0
  await $.session.start({ cwd: '/h/mino-sakura-hq', surface: 'desktop', isInteractive: true })
  expect(git.length).toBe(0)
})
