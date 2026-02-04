export interface KlineBar {
  time: string | number
  open: number
  high: number
  low: number
  close: number
  volume: number
  signal?: 'buy' | 'sell'
}
