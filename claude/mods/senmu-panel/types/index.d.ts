// 専務の操作盤が画面の表示に使う値の型

// 未決事項（私の伺い）1件
export type Pending = { id: string; at: string; text: string }

// 控え帳（業務と関係のない出来事）1件。ファイルに1行1件で残す
export type NoteItem = {
  id: string
  at: string
  pc: string
  source: 'senmu' | 'auto'
  text: string
  status: 'open' | 'done'
  doneAt?: string
  how?: string
}

// 窓の切り替え
export type Tab = 'pending' | 'ask' | 'notes'

declare module 'claude-code' {
  interface PluginState {
    'senmu-panel': {
      tab: Tab
      isPullOffered: boolean
      isPullAsked: boolean
      pullStatus: string
      pending: Pending[]
      notes: NoteItem[]
      sideAnswer: string
      isSideBusy: boolean
    }
  }
}
