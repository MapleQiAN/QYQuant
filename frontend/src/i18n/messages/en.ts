const en = {
  common: {
    settings: 'Settings',
    newStrategy: 'New Strategy',
    viewAll: 'View all',
    searchPlaceholder: 'Search strategies, bots...',
    language: 'Language',
    retry: 'Retry'
  },
  settings: {
    title: 'Settings',
    language: 'Language',
    languageHint: 'Choose your interface language.',
    zh: '中文',
    en: 'EN',
    marketStyle: 'Market Color Style',
    marketStyleHint: 'Choose how price moves are colored.',
    marketStyleCn: 'A-share style (red up, green down)',
    marketStyleUs: 'US style (green up, red down)'
  },
  nav: {
    dashboard: 'Dashboard',
    backtests: 'Backtests',
    bots: 'Bots',
    forum: 'Forum'
  },
  dashboard: {
    title: 'Welcome back, {name}',
    subtitle: 'Here is your trading dashboard overview.',
    recentTitle: 'Recent activity'
  },
  backtest: {
    title: 'Backtest Overview',
    statusCompleted: 'Completed',
    refresh: 'Run again',
    export: 'Export report',
    kpiTotalReturn: 'Total return',
    kpiAnnualizedReturn: 'Annualized return',
    kpiSharpe: 'Sharpe ratio',
    kpiMaxDrawdown: 'Max drawdown',
    statWinRate: 'Win rate',
    statProfitFactor: 'Profit factor',
    statTotalTrades: 'Total trades',
    statAvgHolding: 'Avg holding days'
  },
  kline: {
    buySignal: 'Buy signal',
    sellSignal: 'Sell signal',
    timeframes: {
      '1m': '1m',
      '5m': '5m',
      '15m': '15m',
      '1h': '1h',
      '4h': '4h',
      '1d': '1d'
    }
  },
  recent: {
    tabs: {
      strategies: 'Strategies',
      bots: 'Bots'
    },
    trades: 'trades',
    winRate: 'Win rate',
    maxDrawdown: 'Max drawdown',
    updatedAt: 'Updated',
    viewDetails: 'View details',
    deployBot: 'Deploy bot',
    runtime: 'Runtime',
    capital: 'Capital',
    roi: 'ROI',
    viewLogs: 'View logs',
    pause: 'Pause',
    start: 'Start'
  },
  status: {
    draft: 'Draft',
    running: 'Running',
    paused: 'Paused',
    stopped: 'Stopped',
    completed: 'Completed',
    active: 'Active',
    error: 'Error',
    offline: 'Offline'
  },
  strategyNew: {
    title: 'Create Strategy',
    subtitle: 'Start from scratch or import a QYSP package.',
    back: 'Back to dashboard',
    createTitle: 'Create from scratch',
    createHint: 'Define basic info now. You can import a package later.',
    nameLabel: 'Strategy name',
    namePlaceholder: 'e.g. Gold Breakout',
    symbolLabel: 'Primary symbol',
    symbolPlaceholder: 'e.g. XAUUSD',
    tagsLabel: 'Tags',
    tagsPlaceholder: 'e.g. gold, breakout, trend',
    createAction: 'Create strategy',
    resetAction: 'Reset',
    importTitle: 'Import from file',
    importHint: 'Upload a .qys package that includes strategy.json.',
    fileLabel: 'Strategy package',
    filePlaceholder: 'Choose a .qys file',
    fileHelp: 'Supported: .qys (ZIP), max 20 MB.',
    importAction: 'Import strategy',
    createSuccess: 'Strategy created',
    importSuccess: 'Strategy imported',
    nameRequired: 'Strategy name is required',
    symbolRequired: 'Primary symbol is required',
    fileRequired: 'Please choose a strategy file',
    fileSelected: 'Selected file',
    versionLabel: 'Version',
    sizeLabel: 'Size'
  },
  forum: {
    title: 'Forum Pulse',
    publish: 'New post',
    bookmarks: 'My bookmarks'
  },
  upgrade: {
    title: 'Upgrade to Pro',
    description: 'Unlock unlimited backtests, more bot slots, and pro data feeds',
    features: {
      unlimitedBacktests: 'Unlimited backtests',
      botSlots: '10 bot slots',
      realtimeData: 'Real-time market data',
      prioritySupport: 'Priority support'
    },
    price: '$99',
    period: '/mo',
    originalPrice: '$199',
    cta: 'Upgrade now',
    trial: '7-day free trial, cancel anytime'
  },
  progress: {
    title: 'Stats',
    period7: 'Last 7 days',
    period30: 'Last 30 days',
    period90: 'Last 90 days',
    backtestCount: 'Backtests',
    monthlyQuota: 'Monthly quota',
    robotRuntime: 'Bot runtime',
    activeBots: 'Active bots',
    runtimeUnit: 'hours',
    totalProfit: 'Total profit',
    avgWinRate: 'Avg win rate',
    avgHolding: 'Avg holding',
    sharpeRatio: 'Sharpe ratio'
  },
  states: {
    loadingTitle: 'Loading',
    loadingMessage: 'Fetching latest data...',
    emptyTitle: 'No data',
    emptyMessage: 'Nothing to show yet.',
    errorTitle: 'Something went wrong'
  },
  pages: {
    backtestsTitle: 'Backtests',
    backtestsSubtitle: 'Review recent backtest runs and performance.',
    botsTitle: 'Bots',
    botsSubtitle: 'Manage running bots and recent activity.',
    forumTitle: 'Forum',
    forumSubtitle: 'Explore hot posts and community insights.'
  },
  footer: {
    copyright: '© 2026 QY Quant. All rights reserved.',
    help: 'Help Center',
    api: 'API Docs',
    privacy: 'Privacy Policy'
  }
}

export default en

