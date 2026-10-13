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
function mockPull(on: Parameters<Parameters<typeof test>[1]>[1], dirty: string[] = []) {
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
    const isStatus = e.argv.includes('status')
    git.push(`${repo}:${isStatus ? 'status' : 'pull'}`)
    const out = isStatus && dirty.includes(repo) ? ' M a.txt\n' : ''
    return { value: { exitCode: 0, stdout: out, stderr: '' } as never }
  })
  return { files, git }
}

test('その日の最初の起動で全リポジトリを取り込み、同じ日の2回目はしない', async ($, on) => {
  mock.clock(on)
  mock.store(on)
  const { files, git } = mockPull(on)
  await $.session.start({ cwd: '/h/mino-sakura-hq', surface: 'desktop', isInteractive: true })
  expect(git.filter(g => g.endsWith(':pull'))).toEqual(['mino-sakura-hq:pull', 'dotfiles:pull'])
  expect(files.get('/h/.claude/state/senmu-pull-result.txt')?.includes('取り込み済み 2件')).toBe(true)
  git.length = 0
  await $.session.start({ cwd: '/h/mino-sakura-hq', surface: 'desktop', isInteractive: true })
  expect(git.length).toBe(0)
})

test('保存していない変更があるリポジトリは取り込まず、私への指示に伺いを足す', async ($, on) => {
  mock.clock(on)
  mock.store(on)
  const { git } = mockPull(on, ['dotfiles'])
  on('prompt.submit', ($, e) => ({ text: e.text, context: e.context }))
  await $.session.start({ cwd: '/h/mino-sakura-hq', surface: 'desktop', isInteractive: true })
  expect(git.includes('dotfiles:pull')).toBe(false)
  // 最初の依頼に、私あての知らせ（専務の画面には出ない）として添わる。2回目の依頼には添えない
  const r1 = await $.prompt.submit({ text: '定例業務' } as never)
  expect((r1.context ?? []).some(c => c.includes('dotfiles'))).toBe(true)
  const r2 = await $.prompt.submit({ text: '次の依頼' } as never)
  expect((r2.context ?? []).length).toBe(0)
})
