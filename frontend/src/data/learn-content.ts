export const learnContentByLocale = {
  zh: {
    badge: '量化课程',
    title: '用研究终端的方式学习量化，而不是堆概念',
    subtitle:
      '这份课程手册参考 Quant Wiki 的知识结构，把市场、数据、参数、风控、执行和 AI 策略串成一条可执行的研究链。目标不是背术语，而是知道每个参数在真实研究里控制了什么。',
    stats: [
      { label: '课程模块', value: '7', detail: '从研究地图到 AI 策略工作流' },
      { label: '参数词条', value: '20+', detail: '覆盖回测、因子、风险、微观结构和机器学习' },
      { label: '输出目标', value: '可验证策略', detail: '假设、回测、风控、执行和复盘闭环' },
    ],
    principles: [
      '先定义假设，再优化参数。',
      '先测交易约束，再谈收益曲线。',
      'AI 放大研究效率，不能替代研究纪律。',
    ],
    syllabus: [
      { id: 'research-map', label: '研究地图', meta: '市场 / 数据 / 信号 / 执行' },
      { id: 'research-loop', label: '研究流程', meta: '从假设到复盘' },
      { id: 'parameter-manual', label: '参数词典', meta: '回测 / 因子 / 风险 / 微观结构' },
      { id: 'risk-console', label: '指标与风控', meta: '收益质量而非只看斜率' },
      { id: 'ai-lab', label: 'AI 策略工作流', meta: 'NLP / 监督学习 / GenAI / 合规' },
      { id: 'execution-roadmap', label: '训练路线', meta: '8 周输出一个可解释原型' },
      { id: 'field-notes', label: '延伸阅读', meta: '继续深挖 Quant Wiki' },
    ],
    sections: [
      {
        id: 'research-map',
        eyebrow: 'Research Map',
        title: '先搭研究地图，再学策略细节',
        description:
          '入门阶段要先知道自己在市场规则、数据处理、信号生成、执行约束和组合控制的哪一层工作。Quant Wiki 的价值正是把这些层级组织成可导航的知识图谱。',
        kind: 'map',
        cards: [
          {
            title: '市场与产品层',
            text: '股票、期货、期权、外汇、加密资产在杠杆、保证金、交易时段和流动性上差异很大。很多“策略失效”其实是把一种市场的假设错误迁移到了另一种市场。',
            tags: ['交易时段', '保证金', '流动性'],
          },
          {
            title: '数据与标签层',
            text: 'OHLCV、复权、停牌、另类数据时间戳和标签周期必须先校准。标签一旦偷看未来，后面的回测和训练都没有意义。',
            tags: ['OHLCV', '复权', '标签窗口'],
          },
          {
            title: '策略与因子层',
            text: '趋势、均值回归、横截面因子、事件驱动和统计套利是常见主线。真正值得保留的信号，不是“回测漂亮”，而是能解释经济含义和风险来源。',
            tags: ['趋势', '因子', '事件驱动'],
          },
          {
            title: '执行与组合层',
            text: '研究结论不等于可交易收益。仓位上限、换手约束、交易成本、相关性暴露和风险预算决定策略能否进入真实资金体系。',
            tags: ['仓位', '换手', '风险预算'],
          },
        ],
      },
      {
        id: 'research-loop',
        eyebrow: 'Research Loop',
        title: '量化研究是闭环，不是单次回测',
        description:
          '一轮合格的研究要能回答四件事：为什么这个信号存在、数据是否可信、执行后还剩多少收益、样本外能否站得住。没有闭环，参数越多越像曲线拟合。',
        kind: 'workflow',
        steps: [
          {
            title: '提出可检验假设',
            text: '先写出信号为什么存在：风险补偿、市场摩擦、行为偏差还是信息扩散。假设越具体，后面越知道哪些参数是核心。',
            checkpoint: '输出一句可证伪的研究假设。',
          },
          {
            title: '定义样本与标签',
            text: '锁定交易品种、样本区间、数据频率、持有期和标签周期。AI 策略尤其要先统一 prediction horizon、label horizon 和 rebalance horizon。',
            checkpoint: '写清训练集、验证集、测试集和样本外切分。',
          },
          {
            title: '写成明确交易规则',
            text: '入场、出场、加减仓、止损、调仓频率、权重约束和最大暴露都必须显式化，不要把“看情况”留在代码外。',
            checkpoint: '所有关键规则都能在配置里找到。',
          },
          {
            title: '回测并做稳健性检验',
            text: '除了收益，还要看最大回撤、夏普、换手、成本敏感性、参数扰动和不同市场阶段表现。',
            checkpoint: '至少做一次手续费/滑点扰动和一次样本外验证。',
          },
          {
            title: '仿真执行与复盘',
            text: '进入模拟盘后重点观察延迟、成交偏差、风控阈值和监控报警是否合理。这里暴露的问题通常比历史回测更真实。',
            checkpoint: '形成一份复盘日志，记录偏差来源和修正方案。',
          },
        ],
      },
      {
        id: 'parameter-manual',
        eyebrow: 'Parameter Manual',
        title: '参数词典：把常见参数放回策略上下文',
        description:
          '参数不是越多越高级。好的参数设计应该让你知道它控制了什么风险、牺牲了什么收益、何时容易被误读。下面把最常见的一组参数拆成定义、影响、误区和实战建议。',
        kind: 'parameters',
        groups: [
          {
            title: '回测与执行参数',
            description: '决定你的回测是不是接近真实交易环境。',
            parameters: [
              {
                name: '初始资金',
                definition: '回测开始时假设投入的资金规模，用来决定仓位规模和容量压力。',
                impact: '资金越大，越容易暴露流动性不足和冲击成本。',
                pitfall: '把小资金回测结果线性外推到大资金。',
                practice: '至少做一组不同资金规模的敏感性分析。',
              },
              {
                name: '调仓频率',
                definition: '策略重新计算目标仓位并执行交易的节奏，例如日频、周频、分钟频。',
                impact: '频率越高，手续费、滑点和延迟影响越强。',
                pitfall: '高频更新信号却仍按低成本假设成交。',
                practice: '让标签周期、持有期和调仓频率保持一致。',
              },
              {
                name: '手续费',
                definition: '买卖时支付的佣金、税费和交易所费用。',
                impact: '会直接侵蚀净收益，尤其对高换手策略最敏感。',
                pitfall: '只设置单边手续费，忘记双边交易。',
                practice: '按市场或券商做多组费率情景。',
              },
              {
                name: '滑点',
                definition: '理论成交价与实际可成交价格之间的偏差。',
                impact: '会吞噬短周期 alpha，是检验策略可执行性的关键参数。',
                pitfall: '只在回测末端统一扣一个常数。',
                practice: '让滑点和波动率、成交量或价差相关。',
              },
            ],
          },
          {
            title: '因子与组合参数',
            description: '帮助你理解信号在横截面上的强弱、稳定性以及组合落地方式。',
            parameters: [
              {
                name: '因子暴露',
                definition: '资产或组合相对价值、动量、规模等因子的敏感程度。',
                impact: '决定你赚的是哪类风险溢价，也决定了会在什么市场一起回撤。',
                pitfall: '以为买了很多股票就是分散，忽略它们暴露在同一个因子上。',
                practice: '同时监控行业、风格和单因子集中度。',
              },
              {
                name: 'IC / Rank IC',
                definition: '衡量因子排序与未来收益排序之间相关性的指标，Rank IC 对极端值更稳健。',
                impact: 'IC 反映信号预测力，稳定 IC 往往比一次性高收益更有研究价值。',
                pitfall: '只看均值，不看波动和衰减速度。',
                practice: '同时跟踪 IC 均值、ICIR 和分层收益图。',
              },
              {
                name: '中性化',
                definition: '剔除行业、市值或风格等共同暴露，让信号更聚焦目标 alpha。',
                impact: '能降低意外押注，但也可能把真实有效信号一起洗掉。',
                pitfall: '默认对所有因子都做强中性化。',
                practice: '先明确你想保留什么暴露，再决定对哪些维度中性化。',
              },
              {
                name: '换手率',
                definition: '组合在一定周期内调整仓位的幅度，通常与交易成本高度相关。',
                impact: '换手越高，对手续费、滑点和容量越敏感。',
                pitfall: '把高换手当成更灵敏，却不看成本后的收益。',
                practice: '同时看换手率和单位换手创造的 alpha。',
              },
            ],
          },
          {
            title: '风险与绩效参数',
            description: '这些指标决定策略是否值得继续研究或进入模拟盘。',
            parameters: [
              {
                name: '最大回撤',
                definition: '净值从峰值跌到随后低点的最大跌幅。',
                impact: '决定真实资金最难熬的时刻，也是很多策略被迫终止的原因。',
                pitfall: '只看最大值，不看回撤持续时间和修复时间。',
                practice: '把回撤深度和回撤修复期一起展示。',
              },
              {
                name: 'Sharpe',
                definition: '超额收益相对波动率的比率，用来衡量单位波动承担下的收益效率。',
                impact: '适合比较类似策略，但对非正态收益和尾部风险不够敏感。',
                pitfall: '把高 Sharpe 当作万能指标。',
                practice: '搭配 Sortino、Calmar 和回撤统计一起看。',
              },
              {
                name: 'Beta',
                definition: '策略相对基准市场波动的敏感度，是衡量系统性风险暴露的常见指标。',
                impact: '高 Beta 可能让你在牛市里看起来表现很好，但本质只是放大市场方向风险。',
                pitfall: '把市场上涨阶段的超额收益误认为纯 alpha。',
                practice: '先拆出 Beta，再判断 alpha 是否真实存在。',
              },
              {
                name: '杠杆 / 保证金',
                definition: '通过借入资金或保证金机制放大持仓规模的约束参数。',
                impact: '会同时放大收益、波动和爆仓风险。',
                pitfall: '只在收益端乘以杠杆，没同步放大回撤和风控阈值。',
                practice: '在回测里显式建模追加保证金和强平规则。',
              },
            ],
          },
          {
            title: '订单簿与 AI 参数',
            description: '解释为什么很多短周期和机器学习策略一上实盘就和回测断层。',
            parameters: [
              {
                name: '订单簿失衡',
                definition: '买一侧与卖一侧挂单量的不对称程度，常用于观察短期供需压力。',
                impact: '可用于高频方向判断，但极易被撤单和虚假挂单噪声污染。',
                pitfall: '把瞬时失衡当成稳定信号。',
                practice: '结合成交量、撤单率和持续时间过滤噪声。',
              },
              {
                name: 'Walk-forward',
                definition: '沿时间轴滚动训练与验证的评估方式，模拟模型在真实时间里不断更新。',
                impact: '比一次性切分更接近实盘，也更容易暴露模型衰减和调参过拟合。',
                pitfall: '先在全样本上确定超参数，再假装做 walk-forward。',
                practice: '把标准化、特征选择和调参都放进滚动窗口内。',
              },
              {
                name: '样本泄漏',
                definition: '训练特征或处理流程中混入未来信息，导致离线结果虚高。',
                impact: '是 AI 策略最常见也最致命的问题，能让模型看起来“神准”。',
                pitfall: '全样本标准化、未来收益字段未滞后、事件时间对齐错误。',
                practice: '从特征生成到归一化都按时间顺序执行，并保留审计日志。',
              },
              {
                name: '概率校准',
                definition: '让模型输出的概率更接近真实发生频率，例如 0.7 真的约等于 70% 发生。',
                impact: '对分类信号、风险预警和阈值决策尤为关键。',
                pitfall: '直接拿未经校准的模型概率作为仓位或风控触发依据。',
                practice: '上线前用独立验证集检查 calibration curve 和阈值稳定性。',
              },
            ],
          },
        ],
      },
      {
        id: 'risk-console',
        eyebrow: 'Risk Console',
        title: '指标与风控：先确认收益质量，再确认收益规模',
        description:
          '收益只是结果，风险和可执行性才是筛掉伪策略的过滤器。这里给出一套更适合初学者建立判断力的核心指标面板。',
        kind: 'metrics',
        metrics: [
          {
            title: '年化收益',
            formula: 'Annualized Return',
            text: '回答“如果按当前节奏复利，一年能赚多少”。适合作为输出目标，不适合作为唯一排序依据。',
            watch: '必须和回撤、波动和容量一起看。',
          },
          {
            title: '波动率',
            formula: 'Volatility',
            text: '衡量收益序列的波动强弱。高收益如果伴随巨大波动，策略可能只是在承受更大风险。',
            watch: '注意频率换算方式和跳跃风险被低频数据掩盖的问题。',
          },
          {
            title: 'Sortino / Calmar',
            formula: 'Downside Ratios',
            text: 'Sortino 更关注下行波动，Calmar 用年化收益对比最大回撤，适合补足 Sharpe 对尾部风险不敏感的问题。',
            watch: '收益分布偏态明显时，这两个指标通常更有解释力。',
          },
          {
            title: 'Alpha / Beta 拆解',
            formula: 'Excess Attribution',
            text: '先把策略对市场方向的依赖拆出来，再看真正独立于基准的超额收益有多少。',
            watch: '如果高收益主要来自高 Beta，本质可能只是放大了市场敞口。',
          },
        ],
        checklist: [
          '先做样本外验证，再做参数优化；顺序反了通常就是过拟合。',
          '把风险规则写成硬约束，例如最大回撤阈值和行业权重上限。',
          '记录回撤持续时间、恢复期和不同市场阶段表现，而不只是一张净值图。',
          '任何准备进入实盘的策略，都要重新审视容量、冲击成本和监控告警设计。',
        ],
      },
      {
        id: 'ai-lab',
        eyebrow: 'AI Lab',
        title: 'AI 策略工作流：把机器学习放进量化研究纪律里',
        description:
          '参考 Quant Wiki 的 AI 量化内容，AI 在量化里的价值主要体现在文本理解、特征抽取、组合优化、风险预警和研究辅助。它能提升“快、准、稳”，但前提是你能控制黑箱、数据偏差和合规风险。',
        kind: 'ai',
        modules: [
          {
            title: '文本与另类数据信号',
            text: 'LLM 和 NLP 可以处理新闻、公告、财报电话会和社交媒体，从大规模文本中提取情绪、主题和异常事件。',
            useCases: ['事件驱动信号', '情绪因子', '公告摘要与分歧检测'],
            controls: ['核对时间戳', '保留原文证据', '不要把摘要结果直接当交易指令'],
          },
          {
            title: '监督学习与特征工程',
            text: '树模型、线性模型和序列模型常用于把价格、成交量、因子和宏观变量组合成预测器。真正困难的部分不是换模型，而是定义稳定标签和做干净的时间切分。',
            useCases: ['收益方向预测', '波动率预测', '风险预警评分'],
            controls: ['Walk-forward', '样本泄漏审计', '滚动特征重要性监控'],
          },
          {
            title: '生成式 AI 研究助手',
            text: '生成式 AI 更适合做研究加速器，例如读研报、总结财报、补齐文档和生成实验报告草稿，而不是脱离约束地直接给出买卖决定。',
            useCases: ['研究资料摘要', '实验日志整理', '合规文档初稿'],
            controls: ['人工审校', '敏感信息脱敏', '保存中间推理与引用来源'],
          },
        ],
        governance: [
          '可解释性不是可选项，任何进入投资决策链的模型都应保留版本和决策日志。',
          '如果数据源带有错误或过时内容，AI 只会把偏差放大得更快。',
          'AI 生成的合规或研究文档必须经过人工复核，不能把“模型建议”当作合规答案。',
          '模型上线后要监控漂移、阈值稳定性和市场结构变化，而不是只盯训练集指标。',
        ],
      },
      {
        id: 'execution-roadmap',
        eyebrow: 'Execution Roadmap',
        title: '8 周训练路线：做出第一个可解释原型',
        description:
          '入门阶段不追求“一口气学完量化”。更现实的目标是 8 周内做出一套有假设、有参数、有回测、有样本外验证、有风控规则的策略原型。',
        kind: 'roadmap',
        roadmap: [
          { window: '第 1-2 周', focus: '市场与回测底层', output: '搞清收益率、复权、成交成本、杠杆和回测参数含义。' },
          { window: '第 3-4 周', focus: '数据处理与研究日志', output: '完成行情清洗、标签对齐和特征生成，并记录实验过程。' },
          { window: '第 5-6 周', focus: '策略原型与参数面板', output: '完成一套趋势、均值回归或因子策略，输出核心配置。' },
          { window: '第 7-8 周', focus: 'AI 扩展与仿真执行', output: '加入 AI 辅助研究或简单监督学习模块，完成 walk-forward 和模拟盘复盘。' },
        ],
      },
      {
        id: 'field-notes',
        eyebrow: 'Field Notes',
        title: '延伸阅读：按专题继续深化你的研究栈',
        description:
          '如果你已经能读懂上面的参数和流程，接下来就可以把 Quant Wiki 当作知识索引，按专题深挖。优先顺序建议是先巩固风险与执行，再扩展因子、AI、期权或高频。',
        kind: 'resources',
        resources: [
          { title: 'Quant Wiki 首页', text: '适合作为总导航，快速进入 AI 量化、因子投资、期权、期货、加密和高频等专题。', href: 'https://quant-wiki.com/' },
          { title: 'AI 量化专题', text: '关注生成式 AI、文本分析、组合优化、风险预警和合规问题。', href: 'https://quant-wiki.com/ai/ai-quant/' },
          { title: '入门书单', text: '适合补系统化基础，把金融、数学和工程实现各补一轮。', href: 'https://quant-wiki.com/library/book/beginner/' },
        ],
        pitfalls: [
          '一上来就追复杂模型，却没有先做可解释的基准策略。',
          '把回测平台输出当成真相，没有核查数据口径和成交时点。',
          '没有研究日志，导致调参过程和失败原因不可复盘。',
          '直接把历史最优参数带去实盘，没有经过仿真和样本外检查。',
        ],
      },
    ],
  },
  en: {
    badge: 'Quant Course',
    title: 'Learn quant through a research terminal, not a pile of isolated terms',
    subtitle:
      'This course manual follows Quant Wiki and turns markets, data, parameters, risk, execution, and AI strategy into one practical research chain.',
    stats: [
      { label: 'Modules', value: '7', detail: 'From research map to AI workflow' },
      { label: 'Parameters', value: '20+', detail: 'Backtest, factor, risk, microstructure, and ML settings' },
      { label: 'Target', value: 'Verifiable strategy', detail: 'Hypothesis, backtest, execution, and review in one loop' },
    ],
    principles: [
      'Define the hypothesis before tuning the parameters.',
      'Test execution constraints before trusting the equity curve.',
      'AI improves speed, not discipline.',
    ],
    syllabus: [
      { id: 'research-map', label: 'Research Map', meta: 'Markets / Data / Signals / Execution' },
      { id: 'research-loop', label: 'Research Loop', meta: 'Hypothesis to review' },
      { id: 'parameter-manual', label: 'Parameter Manual', meta: 'Backtest / Factor / Risk / Microstructure' },
      { id: 'risk-console', label: 'Risk Console', meta: 'Read quality before size' },
      { id: 'ai-lab', label: 'AI Strategy Workflow', meta: 'NLP / ML / GenAI / governance' },
      { id: 'execution-roadmap', label: 'Roadmap', meta: 'Build one explainable prototype in 8 weeks' },
      { id: 'field-notes', label: 'Further Reading', meta: 'Go deeper with Quant Wiki' },
    ],
    sections: [],
  },
} as const
