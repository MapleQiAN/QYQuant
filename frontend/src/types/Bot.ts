export type BotStatus = 'active' | 'paused' | 'error' | 'offline'

export interface Bot {
  id: string
  name: string
  strategy: string
  status: BotStatus
  profit: number
  runtime: string
  capital: number
  tags: string[]
}
