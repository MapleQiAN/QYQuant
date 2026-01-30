import type { BacktestLatestResponse } from '../types/Backtest'
import type { Bot } from '../types/Bot'
import type { Strategy } from '../types/Strategy'
import type { Post } from '../types/Post'

export const latestBacktest: BacktestLatestResponse = {
  summary: {
    totalReturn: 12.4,
    annualizedReturn: 24.8,
    sharpeRatio: 1.6,
    maxDrawdown: -6.2,
    winRate: 61.5,
    profitFactor: 1.9,
    totalTrades: 128,
    avgHoldingDays: 2.8
  },
  kline: [
    { time: '09:30', open: 2850, high: 2865, low: 2845, close: 2860, volume: 12500 },
    { time: '09:45', open: 2860, high: 2875, low: 2855, close: 2870, volume: 15000, signal: 'buy' },
    { time: '10:00', open: 2870, high: 2885, low: 2865, close: 2880, volume: 18000 }
  ],
  trades: [
    { id: 'tr-1', symbol: 'XAUUSD', side: 'buy', price: 2860, quantity: 1, pnl: 120, timestamp: '2026-01-29T09:45:00Z' },
    { id: 'tr-2', symbol: 'XAUUSD', side: 'sell', price: 2880, quantity: 1, pnl: 200, timestamp: '2026-01-29T10:00:00Z' }
  ]
}

export const recentBots: Bot[] = [
  {
    id: 'bot-001',
    name: 'Gold Hunter Pro',
    strategy: 'Trend Follow',
    status: 'active',
    profit: 12580.5,
    runtime: '15d 8h',
    capital: 100000,
    tags: ['live', 'vip']
  },
  {
    id: 'bot-002',
    name: 'BTC Grid',
    strategy: 'Grid BTCUSDT',
    status: 'paused',
    profit: 3250.8,
    runtime: '7d 12h',
    capital: 50000,
    tags: ['live']
  }
]

export const recentStrategies: Strategy[] = [
  {
    id: 'str-001',
    name: 'Gold Trend',
    symbol: 'XAUUSD',
    status: 'completed',
    returns: 23.5,
    winRate: 68.5,
    maxDrawdown: -8.3,
    tags: ['trend', 'gold', 'swing'],
    lastUpdate: '2026-01-29 14:30',
    trades: 156
  },
  {
    id: 'str-002',
    name: 'BTC Grid',
    symbol: 'BTCUSDT',
    status: 'running',
    returns: 15.8,
    winRate: 72.3,
    maxDrawdown: -5.2,
    tags: ['grid', 'crypto', 'short'],
    lastUpdate: '2026-01-29 15:45',
    trades: 342
  }
]

export const hotPosts: Post[] = [
  {
    id: 'post-001',
    title: 'MACD-based gold strategy improvements',
    author: 'QuantMaster',
    avatar: 'QM',
    likes: 128,
    comments: 45,
    timestamp: '2h ago',
    tags: ['strategy', 'gold']
  },
  {
    id: 'post-002',
    title: '2026 crypto market outlook and adjustments',
    author: 'CryptoKing',
    avatar: 'CK',
    likes: 256,
    comments: 89,
    timestamp: '5h ago',
    tags: ['market', 'crypto']
  }
]
