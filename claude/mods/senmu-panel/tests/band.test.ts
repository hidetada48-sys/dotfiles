// 未決事項の試験：伺いで終わった返答だけが未決事項に載る
import { expect, mock, test } from 'claude-code/testing'

const PANE = { plugin: 'senmu-panel', component: 'Pane', requestId: 'senmu-panel' } as const

test('伺いで終わると未決事項に載る', async ($, on) => {
  mock.clock(on)
  mock.store(on)
  on('turn.complete', ($, e) => ({ text: e.answer }))
  // ファイルの読み書きは、試験の中だけの入れ物で代わりに受ける
  mock.env(on, { HOME: '/h' })
  const files = new Map<string, string>()
  on('fs.exists', ($, e) => ({ value: files.has(e.path) }))
  on('fs.read', ($, e) => ({ value: files.get(e.path) ?? '' }))
  on('fs.write', ($, e) => {
    files.set(e.path, e.text)
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
  on('fs.exists', ($, e) => ({ value: files.has(e.path) }))
  on('fs.read', ($, e) => ({ value: files.get(e.path) ?? '' }))
  on('fs.write', ($, e) => {
    files.set(e.path, e.text)
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
  on('fs.exists', ($, e) => ({ value: files.has(e.path) }))
  on('fs.read', ($, e) => ({ value: files.get(e.path) ?? '' }))
  on('fs.write', ($, e) => {
    files.set(e.path, e.text)
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
