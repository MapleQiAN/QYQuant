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
    id: 'volatility',
    category: 'core-metrics',
    question: '波动率',
    answer: '波动率衡量策略收益率的波动幅度。波动率越高，说明净值曲线起伏越大，风险也越高；越低则越平稳。',
    relatedMetricKey: 'volatility',
  },
  {
    id: 'sortino-ratio',
    category: 'core-metrics',
    question: '索提诺比率',
    answer: '索提诺比率只把"向下的波动"算作风险，向上的涨不算。它比夏普比率更适合衡量"跌的时候有多疼"。',
    relatedMetricKey: 'sortino_ratio',
  },
  {
    id: 'calmar-ratio',
    category: 'core-metrics',
    question: '卡尔马比率',
    answer: '卡尔马比率是年化收益率除以最大回撤，回答的是"每承受一份最大跌幅，换来多少年化收益"。越高越好。',
    relatedMetricKey: 'calmar_ratio',
  },
  {
    id: 'max-consecutive-losses',
    category: 'core-metrics',
    question: '最大连续亏损次数',
    answer: '最大连续亏损次数表示策略历史上连续亏钱的最长链条。它能帮你评估实盘时能否扛住心理压力。',
    relatedMetricKey: 'max_consecutive_losses',
  },
  {
    id: 'total-trades',
    category: 'core-metrics',
    question: '总交易次数',
    answer: '总交易次数是策略在整个回测期间一共发了多少笔交易。次数太少可能不具统计意义，太多可能过度拟合。',
    relatedMetricKey: 'total_trades',
  },
  {
    id: 'alpha',
    category: 'core-metrics',
    question: '阿尔法 (Alpha)',
    answer: '阿尔法衡量策略超越市场基准的"超额收益"部分。阿尔法大于0，说明策略本身有独立于市场的赚钱能力。',
    relatedMetricKey: 'alpha',
  },
  {
    id: 'beta',
    category: 'core-metrics',
    question: '贝塔 (Beta)',
    answer: '贝塔衡量策略跟随市场波动的敏感度。贝塔等于1代表和大盘同涨同跌，大于1代表波动更剧烈，小于1则更迟钝。',
    relatedMetricKey: 'beta',
  },
  {
    id: 'profit-factor',
    category: 'core-metrics',
    question: '盈利因子',
    answer: '盈利因子是总盈利除以总亏损。大于1说明赚的比亏的多，越大越好。它是评估策略整体赚钱能力的直观指标。',
    relatedMetricKey: 'profit_factor',
  },
  {
    id: 'expectancy',
    category: 'core-metrics',
    question: '期望值',
    answer: '期望值是平均每笔交易预期赚多少钱。正数代表长期看每笔都在赚钱，负数则代表长期在亏。',
    relatedMetricKey: 'expectancy',
  },
  {
    id: 'max-consecutive-wins',
    category: 'core-metrics',
    question: '最大连续盈利次数',
    answer: '最大连续盈利次数是策略历史上连续赚钱的最长链条。它帮你了解策略最好状态时能连赢多少次。',
    relatedMetricKey: 'max_consecutive_wins',
  },
  {
    id: 'value-at-risk-95',
    category: 'core-metrics',
    question: '风险价值 (VaR 95%)',
    answer: 'VaR 95% 表示在95%的置信度下，单笔交易最大可能亏损多少。它是衡量极端风险的常用指标。',
    relatedMetricKey: 'value_at_risk_95',
  },
  {
    id: 'avg-winning-trade',
    category: 'core-metrics',
    question: '平均盈利交易',
    answer: '平均盈利交易是所有赚钱交易的平均收益金额。它帮你理解"赚钱的时候一般赚多少"。',
    relatedMetricKey: 'avg_winning_trade',
  },
  {
    id: 'avg-losing-trade',
    category: 'core-metrics',
    question: '平均亏损交易',
    answer: '平均亏损交易是所有亏钱交易的平均亏损金额。它帮你理解"亏钱的时候一般亏多少"。',
    relatedMetricKey: 'avg_losing_trade',
  },
  {
    id: 'tracking-error',
    category: 'core-metrics',
    question: '跟踪误差',
    answer: '跟踪误差衡量策略收益率和基准收益率之间的偏差程度。跟踪误差越大，说明策略和基准走得越不一样。',
    relatedMetricKey: 'tracking_error',
  },
  {
    id: 'information-ratio',
    category: 'core-metrics',
    question: '信息比率',
    answer: '信息比率是超额收益除以跟踪误差，衡量的是"每偏离基准一分，换来多少超额回报"。越高说明主动管理越高效。',
    relatedMetricKey: 'information_ratio',
  },
  {
    id: 'excess-return',
    category: 'core-metrics',
    question: '超额收益',
    answer: '超额收益是策略收益率减去基准收益率。正数代表跑赢了基准，负数代表跑输了。',
    relatedMetricKey: 'excess_return',
  },
  {
    id: 'benchmark-total-return',
    category: 'core-metrics',
    question: '基准累计收益',
    answer: '基准累计收益是同期市场基准（如买入持有）的总收益率。用来和策略对比，判断策略是否跑赢了市场。',
    relatedMetricKey: 'benchmark_total_return',
  },
  {
    id: 'buy-sell-ratio',
    category: 'core-metrics',
    question: '买卖比',
    answer: '买卖比是买入信号数量与卖出信号数量的比值。接近1说明多空信号均衡，偏离较大则可能存在偏向。',
    relatedMetricKey: 'buy_sell_ratio',
  },
  {
    id: 'signal-frequency',
    category: 'core-metrics',
    question: '信号频率',
    answer: '信号频率表示策略在每天或每周平均发出多少个交易信号。频率过高可能过度交易，过低可能错失机会。',
    relatedMetricKey: 'signal_frequency',
  },
  {
    id: 'holding-period',
    category: 'core-metrics',
    question: '持仓周期',
    answer: '持仓周期是每笔交易平均持有的时间长度。短线策略通常几天，长线策略可能数周或数月。',
    relatedMetricKey: 'holding_period',
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
