export const learnContentByLocale = {
  zh: {
    badge: '量化入门教学',
    title: '从概念、研究到实盘前验证的完整起点',
    subtitle:
      '基于 Quant Wiki 的知识脉络做了本地化整理，把“先学什么、再做什么、怎么避免踩坑”压缩成一页可执行的入门地图。',
    stats: [
      { label: '学习阶段', value: '4' },
      { label: '核心主题', value: '12+' },
      { label: '实战产出', value: '策略原型' },
    ],
    sections: [
      {
        id: 'framework',
        eyebrow: '知识框架',
        title: '先建立量化研究的认知地图',
        description:
          '先把市场、数据、信号、执行、风控串成完整链条，再进入具体策略。这样后面学因子、机器学习或高频时，不会只会套公式。',
        items: [
          {
            title: '市场与产品基础',
            text: '先区分股票、期货、期权、外汇、加密资产的交易规则，理解杠杆、保证金、交易时段、流动性和滑点。'
          },
          {
            title: '数据与特征工程',
            text: '理解 OHLCV、复权、缺失值、因子暴露、标签定义，知道原始数据如何变成可训练、可回测的特征矩阵。'
          },
          {
            title: '策略与信号生成',
            text: '趋势、均值回归、截面因子、事件驱动、统计套利是常见主线，初学阶段优先掌握一类并能解释其经济含义。'
          },
          {
            title: '执行与组合管理',
            text: '研究结论不能直接等于收益，仓位规模、换手限制、成交成本、相关性控制会决定策略是否能落地。'
          }
        ]
      },
      {
        id: 'workflow',
        eyebrow: '研究流程',
        title: '按研究闭环推进，而不是直接写策略',
        description:
          '量化研究最常见的问题不是“不会写代码”，而是没有闭环。每一轮研究都应该有假设、有验证、有失败记录。',
        steps: [
          {
            title: '提出假设',
            text: '先说明为什么这个信号可能有效，例如趋势延续、均值回归、风险补偿或行为偏差。'
          },
          {
            title: '准备数据',
            text: '确认数据频率、交易品种、样本区间、复权方式与清洗逻辑，并记录哪些字段可能引入未来函数。'
          },
          {
            title: '构建规则',
            text: '明确入场、出场、加减仓、止损止盈、最大持仓和再平衡频率，不要把“直觉”留在代码外。'
          },
          {
            title: '回测与稳健性检验',
            text: '除总收益外，至少同时看回撤、夏普、换手、交易成本敏感性、不同市场阶段表现。'
          },
          {
            title: '仿真与复盘',
            text: '通过模拟盘或纸上交易观察实时执行偏差，确认延迟、滑点、风控阈值和监控告警是否合理。'
          }
        ]
      },
      {
        id: 'metrics',
        eyebrow: '指标与风控',
        title: '先学会看风险，再谈收益',
        description:
          '新手常盯着收益曲线，却忽略收益质量。真正能帮助你筛掉伪策略的，是回撤、风险调整收益和交易约束。',
        metrics: [
          {
            title: '年化收益',
            text: '回答“赚得快不快”，但不能单独使用，因为高收益可能只是承担了更大尾部风险。'
          },
          {
            title: '最大回撤',
            text: '回答“最难熬的时候会亏多少”，它直接决定策略是否适合真实资金。'
          },
          {
            title: '夏普比率',
            text: '衡量单位波动下的收益效率，适合比较同类策略，但要结合收益分布和样本长度一起看。'
          },
          {
            title: '胜率与盈亏比',
            text: '胜率高不代表策略好，关键是单笔盈利是否足够覆盖亏损和成本。'
          },
          {
            title: '换手率与成本',
            text: '很多纸面好看的策略，一加上滑点和手续费就失效，尤其是高频和低流动性资产。'
          },
          {
            title: '仓位与暴露控制',
            text: '控制单品种、单行业、单因子和高相关资产的暴露，避免“看似分散，实际同涨同跌”。'
          }
        ],
        warnings: [
          '警惕未来函数、幸存者偏差和样本内过拟合。',
          '不要只看单一回测区间，至少切分训练期、验证期和样本外区间。',
          '先把风控写成规则，再做收益优化，否则容易不断把策略调到历史最优。'
        ]
      },
      {
        id: 'roadmap',
        eyebrow: '学习路线',
        title: '8 周入门路线图',
        description:
          '目标不是 8 周学完量化，而是 8 周内搭出第一个可解释、可复现、可评估的策略原型。',
        roadmap: [
          {
            week: '第 1-2 周',
            focus: '市场与回测基础',
            deliverable: '搞清楚 K 线、收益率、复权、交易成本、回测指标，能手算简单持仓收益。'
          },
          {
            week: '第 3-4 周',
            focus: 'Python 与数据处理',
            deliverable: '能用 pandas/Numpy 清洗行情数据、计算移动均线、收益率、波动率等基础特征。'
          },
          {
            week: '第 5-6 周',
            focus: '策略原型与验证',
            deliverable: '完成一个趋势或均值回归策略，产出参数、交易记录、净值曲线和风险指标。'
          },
          {
            week: '第 7-8 周',
            focus: '稳健性与模拟执行',
            deliverable: '补上样本外检验、参数扰动、成本敏感性和简单的仓位规则，形成可复盘报告。'
          }
        ]
      },
      {
        id: 'resources',
        eyebrow: '延伸阅读',
        title: '按主题继续深入',
        description:
          'Quant Wiki 本身覆盖了从入门书单到 AI 量化、因子投资、期权、加密与高频交易的广泛主题，适合后续拓展方向时按专题深挖。',
        resources: [
          {
            title: 'Quant Wiki 首页',
            text: '可快速浏览 AI 量化、因子投资、期权、期货、加密、高频等专题入口。',
            href: 'https://quant-wiki.com/'
          },
          {
            title: '入门书单',
            text: '适合建立系统知识框架，包含经典量化投资与 Python 算法交易相关读物。',
            href: 'https://quant-wiki.com/library/book/beginner/'
          },
          {
            title: 'Python for Algorithmic Trading',
            text: '偏实战的算法交易与数据分析路线，适合会一点 Python 后继续升级。',
            href: 'https://quant-wiki.com/library/book/beginner/'
          }
        ],
        pitfalls: [
          '一开始就追求复杂模型，而不是先做简单可解释策略。',
          '把回测平台输出当真相，不去核查数据口径与交易规则。',
          '没有研究日志，导致参数调整和失败原因无法复盘。',
          '跳过模拟执行，直接把历史最优参数带到实盘。'
        ]
      }
    ]
  },
  en: {
    badge: 'Quant Learning',
    title: 'A practical starting point from concepts to pre-live validation',
    subtitle:
      'This page condenses the knowledge structure behind Quant Wiki into an execution-first beginner guide: what to learn first, what to build next, and what mistakes to avoid.',
    stats: [
      { label: 'Learning stages', value: '4' },
      { label: 'Core topics', value: '12+' },
      { label: 'Output', value: 'Strategy prototype' },
    ],
    sections: [
      {
        id: 'framework',
        eyebrow: 'Framework',
        title: 'Build the research map before learning isolated tricks',
        description:
          'Connect markets, data, signals, execution, and risk into one chain first. That makes later topics like factor models, ML, or HFT easier to place correctly.',
        items: [
          {
            title: 'Market and instrument basics',
            text: 'Understand how stocks, futures, options, FX, and crypto differ in leverage, margin, trading sessions, liquidity, and slippage.'
          },
          {
            title: 'Data and feature engineering',
            text: 'Learn OHLCV structure, adjustments, missing values, factor exposure, and how raw market data becomes usable research features.'
          },
          {
            title: 'Strategy and signal generation',
            text: 'Trend, mean reversion, cross-sectional factors, event-driven signals, and statistical arbitrage are common starting families.'
          },
          {
            title: 'Execution and portfolio management',
            text: 'Research edge is only part of the job. Position sizing, turnover, costs, and correlation control decide whether a strategy can survive reality.'
          }
        ]
      },
      {
        id: 'workflow',
        eyebrow: 'Workflow',
        title: 'Work through a research loop, not just a code loop',
        description:
          'Most beginner problems come from missing process, not missing code. Each iteration should have a hypothesis, data, validation, and a written conclusion.',
        steps: [
          {
            title: 'Form a hypothesis',
            text: 'State why the signal should exist: trend persistence, mean reversion, risk premium, or behavioral bias.'
          },
          {
            title: 'Prepare data',
            text: 'Lock down frequency, instruments, sample window, adjustment rules, and all fields that could leak future information.'
          },
          {
            title: 'Define rules',
            text: 'Write explicit entry, exit, scaling, stop, rebalance, and max exposure rules. Leave as little intuition outside the system as possible.'
          },
          {
            title: 'Backtest and stress-test',
            text: 'Measure returns, drawdowns, Sharpe, turnover, cost sensitivity, and behavior across different market regimes.'
          },
          {
            title: 'Paper trade and review',
            text: 'Use simulation to check execution gaps, delays, risk thresholds, and monitoring before any live capital is involved.'
          }
        ]
      },
      {
        id: 'metrics',
        eyebrow: 'Metrics & Risk',
        title: 'Learn to read risk before you chase return',
        description:
          'A strategy is not good because its equity curve looks steep. Risk-adjusted quality and execution constraints are what filter fragile ideas out.',
        metrics: [
          {
            title: 'Annualized return',
            text: 'Answers how fast the strategy compounds, but tells nothing by itself about path quality or tail risk.'
          },
          {
            title: 'Maximum drawdown',
            text: 'Answers how painful the worst period can be, which is often the most practical survivability metric.'
          },
          {
            title: 'Sharpe ratio',
            text: 'Useful for comparing strategies on efficiency per unit of volatility, but it must be read with sample quality in mind.'
          },
          {
            title: 'Win rate and payoff ratio',
            text: 'High win rate can still be poor if losers are much larger than winners after fees and slippage.'
          },
          {
            title: 'Turnover and cost',
            text: 'Many attractive backtests disappear when realistic commissions, spread, and slippage are applied.'
          },
          {
            title: 'Position and exposure control',
            text: 'Cap exposure by instrument, sector, factor, and correlation so diversification is real instead of cosmetic.'
          }
        ],
        warnings: [
          'Watch for look-ahead bias, survivorship bias, and in-sample overfitting.',
          'Do not rely on a single backtest window. Split training, validation, and out-of-sample periods.',
          'Write risk rules before optimization, otherwise the process drifts toward historical curve fitting.'
        ]
      },
      {
        id: 'roadmap',
        eyebrow: 'Roadmap',
        title: 'An 8-week beginner plan',
        description:
          'The goal is not to master quant in 8 weeks. The goal is to finish with one explainable, reproducible, and measurable strategy prototype.',
        roadmap: [
          {
            week: 'Weeks 1-2',
            focus: 'Market and backtest basics',
            deliverable: 'Understand candles, returns, adjustments, trading costs, and core evaluation metrics.'
          },
          {
            week: 'Weeks 3-4',
            focus: 'Python and data handling',
            deliverable: 'Use pandas and NumPy to clean data and compute moving averages, returns, and volatility features.'
          },
          {
            week: 'Weeks 5-6',
            focus: 'Prototype and evaluate',
            deliverable: 'Build a basic trend-following or mean-reversion strategy with trades, equity curve, and risk metrics.'
          },
          {
            week: 'Weeks 7-8',
            focus: 'Robustness and paper execution',
            deliverable: 'Add out-of-sample checks, parameter perturbation, cost sensitivity, and simple sizing rules.'
          }
        ]
      },
      {
        id: 'resources',
        eyebrow: 'Further Reading',
        title: 'Go deeper by topic',
        description:
          'Quant Wiki covers beginner books as well as AI quant, factor investing, options, crypto, futures, and HFT. Use it as a structured map when you choose your next branch.',
        resources: [
          {
            title: 'Quant Wiki home',
            text: 'Browse topic hubs for AI quant, factors, options, futures, crypto, and high-frequency trading.',
            href: 'https://quant-wiki.com/'
          },
          {
            title: 'Beginner reading list',
            text: 'A starting shelf of classic quant investing and Python-based algorithmic trading references.',
            href: 'https://quant-wiki.com/library/book/beginner/'
          },
          {
            title: 'Python for Algorithmic Trading',
            text: 'A practical path into data-driven trading once your Python fundamentals are in place.',
            href: 'https://quant-wiki.com/library/book/beginner/'
          }
        ],
        pitfalls: [
          'Starting with complex models instead of simple explainable strategies.',
          'Trusting backtest output without checking data and market microstructure assumptions.',
          'Skipping a research log, making later iteration impossible to audit.',
          'Taking the best historical parameters straight into live trading.'
        ]
      }
    ]
  }
} as const
