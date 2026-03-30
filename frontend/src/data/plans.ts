export interface PlanFeature {
  text: string
  included: boolean
}

export interface Plan {
  level: string
  name: string
  price: number
  quota: number | null
  description: string
  featured?: boolean
  features: PlanFeature[]
}

export const PLANS: Plan[] = [
  {
    level: 'free',
    name: 'Free',
    price: 0,
    quota: 10,
    description: '适合零基础入门，体验平台基础功能。',
    features: [
      { text: '10 次回测 / 月', included: true },
      { text: '基础策略库访问', included: true },
      { text: '基础绩效指标', included: true },
      { text: '策略结果导出', included: false },
      { text: '高级回测参数配置', included: false },
      { text: '自定义数据源', included: false },
      { text: '优先技术支持', included: false },
      { text: '高级 API 访问权限', included: false },
    ],
  },
  {
    level: 'go',
    name: 'Go',
    price: 49,
    quota: 50,
    description: '适合初学量化，开始系统性回测研究。',
    features: [
      { text: '50 次回测 / 月', included: true },
      { text: '基础策略库访问', included: true },
      { text: '基础绩效指标', included: true },
      { text: '策略结果导出', included: true },
      { text: '高级回测参数配置', included: false },
      { text: '自定义数据源', included: false },
      { text: '优先技术支持', included: false },
      { text: '高级 API 访问权限', included: false },
    ],
  },
  {
    level: 'plus',
    name: 'Plus',
    price: 199,
    quota: 200,
    description: '适合个人量化爱好者，开展日常回测研究。',
    featured: true,
    features: [
      { text: '200 次回测 / 月', included: true },
      { text: '基础策略库访问', included: true },
      { text: '高级绩效指标分析', included: true },
      { text: '策略结果导出', included: true },
      { text: '高级回测参数配置', included: true },
      { text: '自定义数据源', included: false },
      { text: '优先技术支持', included: false },
      { text: '高级 API 访问权限', included: false },
    ],
  },
  {
    level: 'pro',
    name: 'Pro',
    price: 499,
    quota: 500,
    description: '适合中频研究和更稳定的策略迭代工作。',
    features: [
      { text: '500 次回测 / 月', included: true },
      { text: '完整策略库访问', included: true },
      { text: '高级绩效指标分析', included: true },
      { text: '策略结果导出', included: true },
      { text: '高级回测参数配置', included: true },
      { text: '自定义数据源', included: true },
      { text: '优先技术支持', included: false },
      { text: '高级 API 访问权限', included: false },
    ],
  },
  {
    level: 'ultra',
    name: 'Ultra',
    price: 999,
    quota: null,
    description: '不限回测次数，适合高频研究与团队协作。',
    features: [
      { text: '无限回测次数', included: true },
      { text: '完整策略库访问', included: true },
      { text: '高级绩效指标分析', included: true },
      { text: '策略结果导出', included: true },
      { text: '高级回测参数配置', included: true },
      { text: '自定义数据源', included: true },
      { text: '优先技术支持', included: true },
      { text: '高级 API 访问权限', included: true },
    ],
  },
]
