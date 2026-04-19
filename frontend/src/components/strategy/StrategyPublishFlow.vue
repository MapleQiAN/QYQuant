<template>
  <Transition name="modal">
    <div v-if="open" class="publish-backdrop" @click.self="emit('close')">
      <div class="publish-modal" role="dialog" aria-modal="true" :aria-label="t('strategy.publish.ariaLabel')">
        <header class="modal-header">
          <div>
            <p class="modal-kicker">{{ t('strategy.publish.title') }}</p>
            <h2 class="modal-title">{{ currentStepTitle }}</h2>
          </div>
          <button class="btn btn-secondary" type="button" @click="emit('close')">{{ t('common.close') }}</button>
        </header>

        <section v-if="step === 1" class="modal-body">
          <label class="field">
            <span>{{ t('strategy.publish.titleLabel') }}</span>
            <input
              data-test="publish-title"
              v-model.trim="form.title"
              class="field-input"
              type="text"
              maxlength="200"
              :placeholder="t('strategy.publish.titlePlaceholder')"
            />
          </label>

          <label class="field">
            <span>{{ t('strategy.publish.descriptionLabel') }}</span>
            <textarea
              data-test="publish-description"
              v-model.trim="form.description"
              class="field-input field-textarea"
              rows="5"
              :placeholder="t('strategy.publish.descriptionPlaceholder')"
            />
          </label>

          <label class="field">
            <span>{{ t('strategy.publish.tagsLabel') }}</span>
            <input
              data-test="publish-tags"
              v-model="form.tagsText"
              class="field-input"
              type="text"
              :placeholder="t('strategy.publish.tagsPlaceholder')"
            />
          </label>

          <div v-if="parsedTags.length" class="tag-row">
            <span v-for="tag in parsedTags" :key="tag" class="pill">{{ tag }}</span>
          </div>

          <label class="field">
            <span>{{ t('strategy.publish.categoryLabel') }}</span>
            <QSelect v-model="form.category" :options="categoryOptions" />
          </label>

          <div class="metric-grid">
            <label class="field">
              <span>{{ t('strategy.publish.sharpeRatio') }}</span>
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
              <span>{{ t('strategy.publish.maxDrawdown') }}</span>
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
              <span>{{ t('strategy.publish.totalReturn') }}</span>
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

          <footer class="modal-actions">
            <button data-test="publish-next" class="btn btn-primary" type="button" @click="goToConfirmation">
              {{ t('strategy.publish.continueButton') }}
            </button>
          </footer>
        </section>

        <section v-else-if="step === 2" class="modal-body">
          <div class="explain-card">
            <h3>{{ t('strategy.publish.codeProtectionTitle') }}</h3>
            <p>{{ t('strategy.publish.codeProtectionDesc') }}</p>
          </div>

          <label class="agreement-row">
            <input data-test="publish-agreement" v-model="agreed" type="checkbox" />
            <span>{{ t('strategy.publish.agreementText') }}</span>
          </label>

          <p v-if="submitError" class="message error">{{ submitError }}</p>

          <footer class="modal-actions">
            <button class="btn btn-secondary" type="button" @click="step = 1">{{ t('strategy.publish.backButton') }}</button>
            <button
              data-test="publish-confirm"
              class="btn btn-primary"
              type="button"
              :disabled="!agreed || submitting"
              @click="submit"
            >
              {{ submitting ? t('strategy.publish.submitting') : t('strategy.publish.confirmButton') }}
            </button>
          </footer>
        </section>

        <section v-else class="modal-body success-state">
          <div class="success-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          </div>
          <h3>{{ t('strategy.publish.submittedTitle') }}</h3>
          <p>{{ t('strategy.publish.submittedDesc') }}</p>
          <footer class="modal-actions">
            <button class="btn btn-primary" type="button" @click="emit('close')">{{ t('strategy.publish.doneButton') }}</button>
          </footer>
        </section>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { MarketplacePublishPayload, Strategy } from '../../types/Strategy'
import { QSelect } from '../ui'

defineOptions({ name: 'StrategyPublishFlow' })

const { t } = useI18n()

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

const categoryOptions = computed(() => [
  { value: 'trend-following', label: t('strategy.publish.categoryTrendFollowing') },
  { value: 'mean-reversion', label: t('strategy.publish.categoryMeanReversion') },
  { value: 'momentum', label: t('strategy.publish.categoryMomentum') },
  { value: 'multi-indicator', label: t('strategy.publish.categoryMultiIndicator') },
  { value: 'other', label: t('strategy.publish.categoryOther') }
])

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
  if (step.value === 1) return t('strategy.publish.step1Title')
  if (step.value === 2) return t('strategy.publish.step2Title')
  return t('strategy.publish.step3Title')
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
    localError.value = t('strategy.publish.titleRequired')
    return
  }
  if (!form.description.trim()) {
    localError.value = t('strategy.publish.descriptionRequired')
    return
  }
  if (!parsedTags.value.length) {
    localError.value = t('strategy.publish.tagRequired')
    return
  }
  if (!toFiniteNumber(form.sharpeRatio) && toFiniteNumber(form.sharpeRatio) !== 0) {
    localError.value = t('strategy.publish.sharpeRequired')
    return
  }
  if (!toFiniteNumber(form.maxDrawdown) && toFiniteNumber(form.maxDrawdown) !== 0) {
    localError.value = t('strategy.publish.drawdownRequired')
    return
  }
  if (!toFiniteNumber(form.totalReturn) && toFiniteNumber(form.totalReturn) !== 0) {
    localError.value = t('strategy.publish.returnRequired')
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
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.32);
  padding: var(--spacing-lg);
}

.publish-modal {
  width: min(100%, 560px);
  max-height: min(90vh, 720px);
  overflow-y: auto;
  padding: var(--spacing-lg);
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.modal-kicker {
  margin: 0;
  font-size: var(--font-size-xs);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.modal-title {
  margin: var(--spacing-xs) 0 0;
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.modal-body {
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

.modal-actions {
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

/* ── Modal Transition ── */
.modal-enter-active {
  transition: opacity 0.25s ease;
}
.modal-enter-active .publish-modal {
  transition: transform 0.3s var(--ease-out-expo, cubic-bezier(0.16, 1, 0.3, 1)), opacity 0.25s ease;
}
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-leave-active .publish-modal {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.modal-enter-from {
  opacity: 0;
}
.modal-enter-from .publish-modal {
  transform: scale(0.95) translateY(8px);
  opacity: 0;
}
.modal-leave-to {
  opacity: 0;
}
.modal-leave-to .publish-modal {
  transform: scale(0.95);
  opacity: 0;
}

@media (max-width: 768px) {
  .publish-backdrop {
    padding: var(--spacing-sm);
    align-items: flex-end;
  }

  .publish-modal {
    width: 100%;
    max-height: 85vh;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
