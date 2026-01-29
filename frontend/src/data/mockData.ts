// ============================================
// Mock Data - QY Quant Dashboard
// ============================================

// Types
export interface Strategy {
  id: string
  name: string
  symbol: string
  status: 'running' | 'paused' | 'stopped' | 'completed'
  returns: number
  winRate: number
  maxDrawdown: number
  tags: string[]
  lastUpdate: string
  trades: number
}

export interface Robot {
  id: string
  name: string
  strategy: string
  status: 'active' | 'paused' | 'error' | 'offline'
  profit: number
  runtime: string
  capital: number
  tags: string[]
}

export interface KlineData {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  signal?: 'buy' | 'sell'
}

export interface ForumPost {
  id: string
  title: string
  author: string
  avatar: string
  likes: number
  comments: number
  timestamp: string
  tags: string[]
}

export interface UserStats {
  backtestCount: number
  backtestTarget: number
  robotRuntime: number
  robotRuntimeUnit: string
  totalProfit: number
  profitChange: number
}

// Mock K-line Data
export const mockKlineData: KlineData[] = [
  { time: '09:30', open: 2850, high: 2865, low: 2845, close: 2860, volume: 12500 },
  { time: '09:45', open: 2860, high: 2875, low: 2855, close: 2870, volume: 15000, signal: 'buy' },
  { time: '10:00', open: 2870, high: 2885, low: 2865, close: 2880, volume: 18000 },
  { time: '10:15', open: 2880, high: 2895, low: 2875, close: 2890, volume: 14000 },
  { time: '10:30', open: 2890, high: 2905, low: 2885, close: 2900, volume: 16500 },
  { time: '10:45', open: 2900, high: 2910, low: 2890, close: 2895, volume: 13000 },
  { time: '11:00', open: 2895, high: 2905, low: 2880, close: 2885, volume: 17500, signal: 'sell' },
  { time: '11:15', open: 2885, high: 2895, low: 2875, close: 2890, volume: 11000 },
  { time: '11:30', open: 2890, high: 2910, low: 2885, close: 2905, volume: 19000 },
  { time: '13:00', open: 2905, high: 2920, low: 2900, close: 2915, volume: 21000, signal: 'buy' },
  { time: '13:15', open: 2915, high: 2930, low: 2910, close: 2925, volume: 18500 },
  { time: '13:30', open: 2925, high: 2940, low: 2920, close: 2935, volume: 22000 },
  { time: '13:45', open: 2935, high: 2945, low: 2925, close: 2930, volume: 16000 },
  { time: '14:00', open: 2930, high: 2940, low: 2920, close: 2925, volume: 14500 },
  { time: '14:15', open: 2925, high: 2935, low: 2915, close: 2920, volume: 13500, signal: 'sell' },
  { time: '14:30', open: 2920, high: 2930, low: 2910, close: 2915, volume: 15000 },
  { time: '14:45', open: 2915, high: 2925, low: 2905, close: 2910, volume: 12000 },
  { time: '15:00', open: 2910, high: 2920, low: 2900, close: 2908, volume: 25000 },
]

// Backtest KPI Metrics
export const backtestKPIs = {
  totalReturn: 23.5,
  annualizedReturn: 45.2,
  sharpeRatio: 1.85,
  maxDrawdown: -8.3,
  winRate: 68.5,
  profitFactor: 2.15,
  totalTrades: 156,
  avgHoldingDays: 3.2,
}

// Recent Strategies
export const mockStrategies: Strategy[] = [
  {
    id: 'str-001',
    name: '黄金趋势追踪策略',
    symbol: 'XAUUSD',
    status: 'completed',
    returns: 23.5,
    winRate: 68.5,
    maxDrawdown: -8.3,
    tags: ['趋势', '黄金', '中长线'],
    lastUpdate: '2026-01-29 14:30',
    trades: 156,
  },
  {
    id: 'str-002',
    name: 'BTC 网格交易策略',
    symbol: 'BTCUSDT',
    status: 'running',
    returns: 15.8,
    winRate: 72.3,
    maxDrawdown: -5.2,
    tags: ['网格', '加密货币', '短线'],
    lastUpdate: '2026-01-29 15:45',
    trades: 342,
  },
  {
    id: 'str-003',
    name: 'A股动量反转策略',
    symbol: '沪深300',
    status: 'paused',
    returns: -3.2,
    winRate: 45.6,
    maxDrawdown: -12.8,
    tags: ['动量', 'A股', '日内'],
    lastUpdate: '2026-01-28 09:30',
    trades: 89,
  },
  {
    id: 'str-004',
    name: 'ETH 套利策略',
    symbol: 'ETHUSDT',
    status: 'stopped',
    returns: 8.9,
    winRate: 82.1,
    maxDrawdown: -2.1,
    tags: ['套利', '加密货币'],
    lastUpdate: '2026-01-27 18:00',
    trades: 1256,
  },
]

// Recent Robots
export const mockRobots: Robot[] = [
  {
    id: 'bot-001',
    name: '黄金猎手 Pro',
    strategy: '黄金趋势追踪策略',
    status: 'active',
    profit: 12580.50,
    runtime: '15天 8小时',
    capital: 100000,
    tags: ['实盘', 'VIP'],
  },
  {
    id: 'bot-002',
    name: 'BTC 网格机器人',
    strategy: 'BTC 网格交易策略',
    status: 'active',
    profit: 3250.80,
    runtime: '7天 12小时',
    capital: 50000,
    tags: ['实盘'],
  },
  {
    id: 'bot-003',
    name: '测试机器人 #3',
    strategy: 'A股动量反转策略',
    status: 'paused',
    profit: -580.20,
    runtime: '3天 4小时',
    capital: 20000,
    tags: ['模拟盘'],
  },
  {
    id: 'bot-004',
    name: 'ETH 套利监控',
    strategy: 'ETH 套利策略',
    status: 'error',
    profit: 890.00,
    runtime: '1天 6小时',
    capital: 30000,
    tags: ['实盘', '告警'],
  },
]

// Forum Posts
export const mockForumPosts: ForumPost[] = [
  {
    id: 'post-001',
    title: '分享：基于MACD的黄金策略优化心得',
    author: 'QuantMaster',
    avatar: 'QM',
    likes: 128,
    comments: 45,
    timestamp: '2小时前',
    tags: ['策略分享', '黄金'],
  },
  {
    id: 'post-002',
    title: '2026年加密货币市场展望与策略调整',
    author: 'CryptoKing',
    avatar: 'CK',
    likes: 256,
    comments: 89,
    timestamp: '5小时前',
    tags: ['市场分析', '加密货币'],
  },
  {
    id: 'post-003',
    title: '新手入门：如何编写你的第一个回测策略',
    author: 'TechHelper',
    avatar: 'TH',
    likes: 512,
    comments: 156,
    timestamp: '1天前',
    tags: ['教程', '入门'],
  },
]

// User Statistics
export const mockUserStats: UserStats = {
  backtestCount: 45,
  backtestTarget: 100,
  robotRuntime: 892,
  robotRuntimeUnit: '小时',
  totalProfit: 28650.80,
  profitChange: 12.5,
}

// Navigation Items
export const navItems = [
  { id: 'backtest', label: '回测', icon: 'chart', active: true },
  { id: 'robots', label: '机器人托管区', icon: 'robot', active: false },
  { id: 'plaza', label: '广场', icon: 'users', active: false },
  { id: 'assets', label: '资产', icon: 'wallet', active: false },
]

// User Info
export const mockUser = {
  name: '量化小王子',
  avatar: 'QX',
  level: 'Pro',
  notifications: 3,
}
