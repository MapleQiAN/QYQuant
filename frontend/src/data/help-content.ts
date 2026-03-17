export type HelpCategory = 'basic-concepts' | 'core-metrics' | 'platform-actions'

export interface HelpEntry {
  id: string
  category: HelpCategory
  question: string
  answer: string
  relatedMetricKey?: string
}

export const helpCategories: Array<{ id: 'all' | HelpCategory; label: string }> = [
  { id: 'all', label: '全部' },
  { id: 'basic-concepts', label: '基础概念' },
  { id: 'core-metrics', label: '核心指标' },
  { id: 'platform-actions', label: '平台操作' },
]

export const helpEntries: HelpEntry[] = [
  {
    id: 'what-is-backtest',
    category: 'basic-concepts',
    question: '什么是回测',
    answer: '回测就是用历史行情重放你的策略，看它过去如果这么做，结果会怎样。可以把它理解成“用旧考卷先做一次模拟考试”。',
  },
  {
    id: 'what-is-strategy',
    category: 'basic-concepts',
    question: '什么是策略',
    answer: '策略是一套明确的买卖规则，例如什么时候买、什么时候卖、仓位多大。规则越清晰，越适合量化执行。',
  },
  {
    id: 'what-is-symbol',
    category: 'basic-concepts',
    question: '什么是标的',
    answer: '标的是你要交易或研究的对象，比如黄金、沪深300、某只股票。先选对标的，回测结果才有意义。',
  },
  {
    id: 'sharpe-ratio',
    category: 'core-metrics',
    question: '夏普比率',
    answer: '夏普比率衡量的是“每承担一份波动，换来了多少收益”。同样赚钱时，夏普比率更高，通常代表过程更稳。',
    relatedMetricKey: 'sharpe_ratio',
  },
  {
    id: 'max-drawdown',
    category: 'core-metrics',
    question: '最大回撤',
    answer: '最大回撤表示策略从历史高点往下跌得最深的一次。你可以把它看成账户坐过的最陡的一次过山车，越小通常越安心。',
    relatedMetricKey: 'max_drawdown',
  },
  {
    id: 'total-return',
    category: 'core-metrics',
    question: '累计收益率',
    answer: '累计收益率表示这次回测从开始到结束一共赚了多少百分比。它回答的是“最后一共赚没赚钱、赚了多少”。',
    relatedMetricKey: 'total_return',
  },
  {
    id: 'annualized-return',
    category: 'core-metrics',
    question: '年化收益率',
    answer: '年化收益率把不同长度的回测结果折算到一年，方便横向比较。它更像把短跑成绩换算成标准赛道成绩。',
    relatedMetricKey: 'annualized_return',
  },
  {
    id: 'win-rate',
    category: 'core-metrics',
    question: '胜率',
    answer: '胜率表示所有交易里有多少笔是赚钱的。它高不一定代表最终收益高，还要和盈亏比一起看。',
    relatedMetricKey: 'win_rate',
  },
  {
    id: 'profit-loss-ratio',
    category: 'core-metrics',
    question: '盈亏比',
    answer: '盈亏比看的是平均赚一笔和平均亏一笔谁更大。哪怕胜率一般，只要盈亏比够好，策略也可能整体赚钱。',
    relatedMetricKey: 'profit_loss_ratio',
  },
  {
    id: 'run-backtest',
    category: 'platform-actions',
    question: '如何运行回测',
    answer: '先选策略，再确认标的和时间区间，最后点击运行即可。第一次使用时，跟着引导流程走会更快看到结果。',
  },
  {
    id: 'import-strategy',
    category: 'platform-actions',
    question: '如何导入策略',
    answer: '进入策略广场或策略库后上传 `.qys` 包即可。平台会读取策略元数据和参数定义，方便后续直接回测。',
  },
  {
    id: 'backtest-quota',
    category: 'platform-actions',
    question: '回测额度是什么意思',
    answer: '回测额度表示你当前套餐允许发起多少次回测。它像每月可用次数，避免资源被无限占用。',
  },
]

export function findHelpEntryByMetricKey(metricKey: string) {
  return helpEntries.find((entry) => entry.relatedMetricKey === metricKey)
}
