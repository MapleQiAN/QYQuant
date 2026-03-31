<template>
  <Transition name="drawer">
    <div v-if="open" class="publish-backdrop" @click.self="emit('close')">
    <aside class="publish-drawer" role="dialog" aria-modal="true" aria-label="Publish strategy">
      <header class="drawer-header">
        <div>
          <p class="drawer-kicker">Marketplace Publish</p>
          <h2 class="drawer-title">{{ currentStepTitle }}</h2>
        </div>
        <button class="btn btn-secondary" type="button" @click="emit('close')">Close</button>
      </header>

      <section v-if="step === 1" class="drawer-body">
        <label class="field">
          <span>Title</span>
          <input
            data-test="publish-title"
            v-model.trim="form.title"
            class="field-input"
            type="text"
            maxlength="200"
            placeholder="Strategy title"
          />
        </label>

        <label class="field">
          <span>Description</span>
          <textarea
            data-test="publish-description"
            v-model.trim="form.description"
            class="field-input field-textarea"
            rows="5"
            placeholder="Describe the strategy logic and suitable market conditions"
          />
        </label>

        <label class="field">
          <span>Tags</span>
          <input
            data-test="publish-tags"
            v-model="form.tagsText"
            class="field-input"
            type="text"
            placeholder="Use commas to separate tags"
          />
        </label>

        <div v-if="parsedTags.length" class="tag-row">
          <span v-for="tag in parsedTags" :key="tag" class="pill">{{ tag }}</span>
        </div>

        <label class="field">
          <span>Category</span>
          <select v-model="form.category" class="field-input">
            <option v-for="option in categoryOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>

        <div class="metric-grid">
          <label class="field">
            <span>Sharpe Ratio</span>
            <input
              data-test="publish-sharpe-ratio"
              v-model="form.sharpeRatio"
              class="field-input"
              type="number"
              step="0.01"
              placeholder="1.45"
            />
          </label>
          <label class="field">
            <span>Max Drawdown</span>
            <input
              data-test="publish-max-drawdown"
              v-model="form.maxDrawdown"
              class="field-input"
              type="number"
              step="0.01"
              placeholder="-12.5"
            />
          </label>
          <label class="field">
            <span>Total Return</span>
            <input
              data-test="publish-total-return"
              v-model="form.totalReturn"
              class="field-input"
              type="number"
              step="0.01"
              placeholder="36.8"
            />
          </label>
        </div>

        <p v-if="localError" class="message error">{{ localError }}</p>

        <footer class="drawer-actions">
          <button data-test="publish-next" class="btn btn-primary" type="button" @click="goToConfirmation">
            Continue
          </button>
        </footer>
      </section>

      <section v-else-if="step === 2" class="drawer-body">
        <div class="explain-card">
          <h3>Code protection mechanism</h3>
          <p>
            Your strategy code stays protected on the server. Other users can run the strategy, but they cannot view,
            download, or export the source code.
          </p>
        </div>

        <label class="agreement-row">
          <input data-test="publish-agreement" v-model="agreed" type="checkbox" />
          <span>I confirm I own the strategy and agree to the marketplace IP terms.</span>
        </label>

        <p v-if="submitError" class="message error">{{ submitError }}</p>

        <footer class="drawer-actions">
          <button class="btn btn-secondary" type="button" @click="step = 1">Back</button>
          <button
            data-test="publish-confirm"
            class="btn btn-primary"
            type="button"
            :disabled="!agreed || submitting"
            @click="submit"
          >
            {{ submitting ? 'Submitting...' : 'Confirm publish' }}
          </button>
        </footer>
      </section>

      <section v-else class="drawer-body success-state">
        <div class="success-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        </div>
        <h3>Strategy submitted for review</h3>
        <p>Your strategy is now pending review. You can close this drawer and continue working in your library.</p>
        <footer class="drawer-actions">
          <button class="btn btn-primary" type="button" @click="emit('close')">Done</button>
        </footer>
      </section>
    </aside>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { MarketplacePublishPayload, Strategy } from '../../types/Strategy'

defineOptions({ name: 'StrategyPublishFlow' })

const props = defineProps<{
  open: boolean
  strategy: Strategy | null
  submitting?: boolean
  submitted?: boolean
  submitError?: string
}>()

const emit = defineEmits<{
  (event: 'close'): void
  (event: 'submit', payload: MarketplacePublishPayload): void
}>()

const categoryOptions = [
  { value: 'trend-following', label: 'Trend Following' },
  { value: 'mean-reversion', label: 'Mean Reversion' },
  { value: 'momentum', label: 'Momentum' },
  { value: 'multi-indicator', label: 'Multi Indicator' },
  { value: 'other', label: 'Other' }
]

const step = ref(1)
const agreed = ref(false)
const localError = ref('')
const form = reactive({
  title: '',
  description: '',
  tagsText: '',
  category: 'trend-following',
  sharpeRatio: '',
  maxDrawdown: '',
  totalReturn: ''
})

const parsedTags = computed(() =>
  form.tagsText
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
)

const currentStepTitle = computed(() => {
  if (step.value === 1) return 'Prepare listing details'
  if (step.value === 2) return 'Review code protection terms'
  return 'Submission complete'
})

watch(
  () => [props.open, props.strategy?.id],
  () => {
    if (!props.open || !props.strategy) {
      return
    }
    resetForm()
  },
  { immediate: true }
)

watch(
  () => props.submitted,
  (submitted) => {
    if (submitted) {
      step.value = 3
    }
  }
)

function resetForm() {
  step.value = 1
  agreed.value = false
  localError.value = ''
  form.title = props.strategy?.title || props.strategy?.name || ''
  form.description = props.strategy?.description || ''
  form.tagsText = (props.strategy?.tags || []).join(', ')
  form.category = props.strategy?.category || 'trend-following'
  form.sharpeRatio = ''
  form.maxDrawdown = toPrefillNumber(props.strategy?.maxDrawdown)
  form.totalReturn = toPrefillNumber(props.strategy?.returns)
}

function goToConfirmation() {
  if (!form.title.trim()) {
    localError.value = 'Title is required.'
    return
  }
  if (!form.description.trim()) {
    localError.value = 'Description is required.'
    return
  }
  if (!parsedTags.value.length) {
    localError.value = 'At least one tag is required.'
    return
  }
  if (!toFiniteNumber(form.sharpeRatio) && toFiniteNumber(form.sharpeRatio) !== 0) {
    localError.value = 'Sharpe ratio is required.'
    return
  }
  if (!toFiniteNumber(form.maxDrawdown) && toFiniteNumber(form.maxDrawdown) !== 0) {
    localError.value = 'Max drawdown is required.'
    return
  }
  if (!toFiniteNumber(form.totalReturn) && toFiniteNumber(form.totalReturn) !== 0) {
    localError.value = 'Total return is required.'
    return
  }
  localError.value = ''
  step.value = 2
}

function submit() {
  if (!props.strategy) {
    return
  }

  emit('submit', {
    strategyId: props.strategy.id,
    title: form.title.trim(),
    description: form.description.trim(),
    tags: parsedTags.value,
    category: form.category,
    displayMetrics: {
      sharpe_ratio: toFiniteNumber(form.sharpeRatio) ?? 0,
      max_drawdown: toFiniteNumber(form.maxDrawdown) ?? 0,
      total_return: toFiniteNumber(form.totalReturn) ?? 0
    }
  })
}

function toFiniteNumber(value: string | number | null | undefined) {
  const numeric = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

function toPrefillNumber(value: string | number | null | undefined) {
  return typeof value === 'number' && Number.isFinite(value) ? String(value) : ''
}
</script>

<style scoped>
.publish-backdrop {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  justify-content: flex-end;
  background: rgba(15, 23, 42, 0.32);
}

.publish-drawer {
  width: min(100%, 520px);
  height: 100%;
  overflow-y: auto;
  padding: var(--spacing-lg);
  background: var(--color-surface);
  border-left: 1px solid var(--color-border-light);
  box-shadow: var(--shadow-lg);
}

.drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.drawer-kicker {
  margin: 0;
  font-size: var(--font-size-xs);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.drawer-title {
  margin: var(--spacing-xs) 0 0;
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.drawer-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  color: var(--color-text-primary);
}

.field-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-primary);
}

.field-textarea {
  resize: vertical;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.pill {
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--color-background);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.explain-card {
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
  background: var(--color-background);
}

.explain-card h3,
.success-state h3 {
  margin: 0;
  color: var(--color-text-primary);
}

.explain-card p,
.success-state p {
  margin: var(--spacing-sm) 0 0;
  color: var(--color-text-secondary);
}

.agreement-row {
  display: flex;
  gap: var(--spacing-sm);
  align-items: flex-start;
  color: var(--color-text-secondary);
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}

.message.error {
  color: var(--color-danger);
}

/* ── Success State ── */
.success-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--color-success-bg);
  color: var(--color-success);
  margin-bottom: var(--spacing-md);
}

.success-state {
  align-items: center;
  text-align: center;
}

/* ── Drawer Transition ── */
.drawer-enter-active {
  transition: opacity 0.25s ease;
}
.drawer-enter-active .publish-drawer {
  transition: transform 0.3s var(--ease-out-expo, cubic-bezier(0.16, 1, 0.3, 1));
}
.drawer-leave-active {
  transition: opacity 0.2s ease;
}
.drawer-leave-active .publish-drawer {
  transition: transform 0.2s ease;
}
.drawer-enter-from {
  opacity: 0;
}
.drawer-enter-from .publish-drawer {
  transform: translateX(100%);
}
.drawer-leave-to {
  opacity: 0;
}
.drawer-leave-to .publish-drawer {
  transform: translateX(100%);
}

@media (max-width: 768px) {
  .publish-drawer {
    width: 100%;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
