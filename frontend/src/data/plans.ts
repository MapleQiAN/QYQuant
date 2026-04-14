export const PLAN_TIER_ORDER: Record<string, number> = {
  free: 0,
  go: 1,
  plus: 2,
  pro: 3,
  ultra: 4,
}

export interface PlanFeature {
  text: string
  included: boolean
}

export interface Plan {
  level: string
  name: string
  price: number
  promoPrice?: number
  quota: number | null
  botLimit: number
  description: string
  featured?: boolean
  features: PlanFeature[]
}

interface PlanFeatureDef {
  textKey: string
  included: boolean
}

interface PlanDef {
  level: string
  name: string
  price: number
  promoPrice?: number
  quota: number | null
  botLimit: number
  descriptionKey: string
  featured?: boolean
  features: PlanFeatureDef[]
}

type Translate = (key: string, params?: Record<string, unknown>) => string

const PLAN_DEFS: PlanDef[] = [
  {
    level: 'free',
    name: 'Free',
    price: 0,
    quota: 10,
    botLimit: 1,
    descriptionKey: 'pricing.planDescriptions.free',
    features: [
      { textKey: 'pricing.features.backtests10', included: true },
      { textKey: 'pricing.features.basicLibrary', included: true },
      { textKey: 'pricing.features.basicMetrics', included: true },
      { textKey: 'pricing.features.exportResults', included: false },
      { textKey: 'pricing.features.advancedParams', included: false },
      { textKey: 'pricing.features.customDataSource', included: false },
      { textKey: 'pricing.features.prioritySupport', included: false },
      { textKey: 'pricing.features.advancedApi', included: false },
    ],
  },
  {
    level: 'go',
    name: 'Go',
    price: 49,
    promoPrice: 29,
    quota: 50,
    botLimit: 1,
    descriptionKey: 'pricing.planDescriptions.go',
    features: [
      { textKey: 'pricing.features.backtests50', included: true },
      { textKey: 'pricing.features.basicLibrary', included: true },
      { textKey: 'pricing.features.basicMetrics', included: true },
      { textKey: 'pricing.features.exportResults', included: true },
      { textKey: 'pricing.features.advancedParams', included: false },
      { textKey: 'pricing.features.customDataSource', included: false },
      { textKey: 'pricing.features.prioritySupport', included: false },
      { textKey: 'pricing.features.advancedApi', included: false },
    ],
  },
  {
    level: 'plus',
    name: 'Plus',
    price: 199,
    promoPrice: 99,
    quota: 200,
    botLimit: 2,
    descriptionKey: 'pricing.planDescriptions.plus',
    featured: true,
    features: [
      { textKey: 'pricing.features.backtests200', included: true },
      { textKey: 'pricing.features.basicLibrary', included: true },
      { textKey: 'pricing.features.advancedMetrics', included: true },
      { textKey: 'pricing.features.exportResults', included: true },
      { textKey: 'pricing.features.advancedParams', included: true },
      { textKey: 'pricing.features.customDataSource', included: false },
      { textKey: 'pricing.features.prioritySupport', included: false },
      { textKey: 'pricing.features.advancedApi', included: false },
    ],
  },
  {
    level: 'pro',
    name: 'Pro',
    price: 499,
    promoPrice: 259,
    quota: 500,
    botLimit: 3,
    descriptionKey: 'pricing.planDescriptions.pro',
    features: [
      { textKey: 'pricing.features.backtests500', included: true },
      { textKey: 'pricing.features.fullLibrary', included: true },
      { textKey: 'pricing.features.advancedMetrics', included: true },
      { textKey: 'pricing.features.exportResults', included: true },
      { textKey: 'pricing.features.advancedParams', included: true },
      { textKey: 'pricing.features.customDataSource', included: true },
      { textKey: 'pricing.features.prioritySupport', included: false },
      { textKey: 'pricing.features.advancedApi', included: false },
    ],
  },
  {
    level: 'ultra',
    name: 'Ultra',
    price: 999,
    promoPrice: 599,
    quota: null,
    botLimit: 5,
    descriptionKey: 'pricing.planDescriptions.ultra',
    features: [
      { textKey: 'pricing.unlimitedBacktests', included: true },
      { textKey: 'pricing.features.fullLibrary', included: true },
      { textKey: 'pricing.features.advancedMetrics', included: true },
      { textKey: 'pricing.features.exportResults', included: true },
      { textKey: 'pricing.features.advancedParams', included: true },
      { textKey: 'pricing.features.customDataSource', included: true },
      { textKey: 'pricing.features.prioritySupport', included: true },
      { textKey: 'pricing.features.advancedApi', included: true },
    ],
  },
]

export function buildPlans(t: Translate): Plan[] {
  return PLAN_DEFS.map((plan) => ({
    level: plan.level,
    name: plan.name,
    price: plan.price,
    promoPrice: plan.promoPrice,
    quota: plan.quota,
    botLimit: plan.botLimit,
    description: t(plan.descriptionKey),
    featured: plan.featured,
    features: plan.features.map((feature) => ({
      text: t(feature.textKey),
      included: feature.included,
    })),
  }))
}
