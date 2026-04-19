<template>
  <div class="risk-profile-form">
    <h3 class="form-title">Risk Profile</h3>
    <p class="form-subtitle">Help us tailor the strategy to your risk tolerance.</p>

    <div class="form-grid">
      <div class="form-group">
        <label class="form-label">Max single loss</label>
        <div class="slider-group">
          <input
            type="range"
            class="slider-input"
            :min="1"
            :max="10"
            :step="0.5"
            :value="maxSingleLoss"
            @input="updateField('maxSingleLoss', Number(($event.target as HTMLInputElement).value))"
          />
          <div class="slider-info">
            <span class="slider-bound">1%</span>
            <span class="slider-current">{{ maxSingleLoss }}%</span>
            <span class="slider-bound">10%</span>
          </div>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Position ratio</label>
        <div class="slider-group">
          <input
            type="range"
            class="slider-input"
            :min="0.1"
            :max="1"
            :step="0.1"
            :value="positionRatio"
            @input="updateField('positionRatio', Number(($event.target as HTMLInputElement).value))"
          />
          <div class="slider-info">
            <span class="slider-bound">10%</span>
            <span class="slider-current">{{ Math.round(positionRatio * 100) }}%</span>
            <span class="slider-bound">100%</span>
          </div>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Drawdown tolerance</label>
        <div class="option-group">
          <button
            v-for="opt in drawdownOptions"
            :key="opt.value"
            class="option-btn"
            :class="{ active: drawdownTolerance === opt.value }"
            @click="updateField('drawdownTolerance', opt.value)"
          >
            <span class="option-label">{{ opt.label }}</span>
            <span class="option-desc">{{ opt.desc }}</span>
          </button>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Consecutive loss patience</label>
        <div class="option-group compact">
          <button
            v-for="val in [2, 3, 5, 8]"
            :key="val"
            class="option-btn small"
            :class="{ active: consecutiveLossPatience === val }"
            @click="updateField('consecutiveLossPatience', val)"
          >
            {{ val }}
          </button>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Investment style</label>
        <div class="option-group">
          <button
            v-for="opt in styleOptions"
            :key="opt.value"
            class="option-btn"
            :class="{ active: style === opt.value }"
            @click="updateField('style', opt.value)"
          >
            <span class="option-label">{{ opt.label }}</span>
            <span class="option-desc">{{ opt.desc }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

export interface RiskProfileData {
  maxSingleLoss: number
  positionRatio: number
  drawdownTolerance: 'low' | 'medium' | 'high'
  consecutiveLossPatience: number
  style: 'conservative' | 'balanced' | 'aggressive'
}

const props = withDefaults(defineProps<{
  modelValue?: RiskProfileData
  disabled?: boolean
}>(), {
  disabled: false,
})

const emit = defineEmits<{
  (event: 'update:modelValue', value: RiskProfileData): void
}>()

const state = reactive<RiskProfileData>({
  maxSingleLoss: props.modelValue?.maxSingleLoss ?? 5,
  positionRatio: props.modelValue?.positionRatio ?? 0.5,
  drawdownTolerance: props.modelValue?.drawdownTolerance ?? 'medium',
  consecutiveLossPatience: props.modelValue?.consecutiveLossPatience ?? 3,
  style: props.modelValue?.style ?? 'balanced',
})

const { maxSingleLoss, positionRatio, drawdownTolerance, consecutiveLossPatience, style } = state

const drawdownOptions = [
  { value: 'low' as const, label: 'Low', desc: '5%-10%' },
  { value: 'medium' as const, label: 'Medium', desc: '10%-20%' },
  { value: 'high' as const, label: 'High', desc: '20%-30%' },
]

const styleOptions = [
  { value: 'conservative' as const, label: 'Conservative', desc: 'Capital preservation' },
  { value: 'balanced' as const, label: 'Balanced', desc: 'Risk/reward balance' },
  { value: 'aggressive' as const, label: 'Aggressive', desc: 'Maximize returns' },
]

function updateField(field: keyof RiskProfileData, value: unknown) {
  (state as Record<string, unknown>)[field] = value
}

watch(
  () => ({ ...state }),
  (value) => emit('update:modelValue', { ...value }),
  { deep: true, immediate: true },
)
</script>

<style scoped>
.risk-profile-form {
  padding: var(--spacing-lg);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.form-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.form-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-bottom: var(--spacing-lg);
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-label {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.slider-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.slider-input {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: var(--radius-xs);
  background: var(--color-border-light);
  border: 2px solid var(--color-border);
  outline: none;
  cursor: pointer;
}

.slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--color-accent);
  border: 2px solid var(--color-border);
  cursor: pointer;
}

.slider-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.slider-bound {
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

.slider-current {
  font-size: var(--font-size-xs);
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--color-text-primary);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  border: 2px solid var(--color-border);
  background: var(--color-accent-bg);
}

.option-group {
  display: flex;
  gap: var(--spacing-sm);
}

.option-group.compact {
  gap: var(--spacing-xs);
}

.option-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: var(--spacing-sm);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  cursor: pointer;
  transition: all 0.15s;
}

.option-btn:hover {
  border-color: var(--color-primary-border);
}

.option-btn.active {
  background: var(--color-accent-bg);
  border-color: var(--color-primary-border);
}

.option-btn.small {
  padding: var(--spacing-xs) var(--spacing-md);
  font-weight: var(--font-weight-semibold);
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.option-label {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.option-desc {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
</style>
