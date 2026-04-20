<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card">
      <div class="modal-header">
        <div>
          <p class="modal-eyebrow">量化交易</p>
          <h2 class="modal-title">创建量化托管机器人</h2>
          <p class="modal-subtitle">选择你的策略、券商账户和托管金额，生成一个真实托管机器人。</p>
        </div>
        <button class="btn btn-ghost" type="button" @click="$emit('close')">关闭</button>
      </div>

      <div v-if="brokerOptions.length === 0" class="empty-state">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <p>暂无可用券商连接。请先在设置页绑定券商 API 账户。</p>
      </div>

      <template v-else>
        <div class="form-grid">
          <label class="field">
            <span class="field__label">机器人名称</span>
            <input v-model="name" class="field-control" maxlength="64" placeholder="例如：沪深择时一号" type="text" />
          </label>

          <label class="field">
            <span class="field__label">策略</span>
            <QSelect
              v-model="strategyId"
              :options="strategyOptions"
              placeholder="选择策略"
              searchable
            />
          </label>

          <label class="field">
            <span class="field__label">券商账户</span>
            <QSelect
              v-model="integrationId"
              :options="brokerOptions"
              placeholder="选择券商账户"
              searchable
            />
          </label>

          <label class="field">
            <span class="field__label">托管金额</span>
            <input
              v-model.number="capital"
              class="field-control"
              min="1000"
              step="100"
              type="number"
            />
          </label>
        </div>

        <div v-if="accountSummary" class="account-box">
          <div class="account-box__title">账户概览</div>
          <div class="account-grid">
            <div class="account-item">
              <span class="account-item__label">可用资金</span>
              <strong class="account-item__value tnum">{{ formatMoney(accountSummary.available_cash ?? accountSummary.available ?? accountSummary.cash) }}</strong>
            </div>
            <div class="account-item">
              <span class="account-item__label">账户权益</span>
              <strong class="account-item__value tnum">{{ formatMoney(accountSummary.equity) }}</strong>
            </div>
          </div>
        </div>

        <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

        <div class="modal-footer">
          <button
            :disabled="isSubmitting || !strategyId || !integrationId || capital < 1000"
            class="btn btn-accent"
            type="button"
            @click="submit"
          >
            {{ isSubmitting ? '创建中...' : '创建托管机器人' }}
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useBotsStore } from '../../stores/bots'
import { useIntegrationsStore } from '../../stores/useIntegrationsStore'
import { useStrategiesStore } from '../../stores/strategies'
import { QSelect } from '../ui'

const props = withDefaults(defineProps<{
  initialStrategyId?: string
}>(), {
  initialStrategyId: '',
})

const emit = defineEmits<{
  (event: 'close'): void
  (event: 'created'): void
}>()

const botsStore = useBotsStore()
const strategiesStore = useStrategiesStore()
const integrationsStore = useIntegrationsStore()
const { providers, integrations, accountById } = storeToRefs(integrationsStore)

const name = ref('')
const strategyId = ref(props.initialStrategyId)
const integrationId = ref('')
const capital = ref(100000)
const isSubmitting = ref(false)
const errorMessage = ref('')

const providerByKey = computed(() => Object.fromEntries(providers.value.map((item) => [item.key, item])))
const strategyOptions = computed(() =>
  strategiesStore.library.map((strategy) => ({
    label: strategy.title || strategy.name,
    value: strategy.id,
  }))
)
const brokerOptions = computed(() =>
  integrations.value
    .filter((integration) => providerByKey.value[integration.providerKey]?.type === 'broker_account')
    .map((integration) => ({
      label: `${integration.displayName} · ${providerByKey.value[integration.providerKey]?.name ?? integration.providerKey}`,
      value: integration.id,
    }))
)
const accountSummary = computed(() => integrationId.value ? accountById.value[integrationId.value] : undefined)

onMounted(async () => {
  if (!strategiesStore.library.length) {
    await strategiesStore.loadLibrary({ page: 1, perPage: 100 })
  }
  if (!providers.value.length) {
    await integrationsStore.loadProviders()
  }
  if (!integrations.value.length) {
    await integrationsStore.loadIntegrations()
  }
  if (props.initialStrategyId) {
    strategyId.value = props.initialStrategyId
  }
})

watch(
  () => props.initialStrategyId,
  (value) => {
    if (value) {
      strategyId.value = value
    }
  }
)

watch(integrationId, async (value) => {
  if (!value || accountById.value[value]) {
    return
  }
  try {
    await integrationsStore.loadAccount(value)
  } catch {
    // keep modal usable even if broker account summary cannot be loaded
  }
})

async function submit() {
  if (!strategyId.value || !integrationId.value || capital.value < 1000 || isSubmitting.value) {
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''

  try {
    await botsStore.createBot({
      name: name.value.trim(),
      strategyId: strategyId.value,
      integrationId: integrationId.value,
      capital: capital.value,
    })
    emit('created')
  } catch (error: any) {
    errorMessage.value = error?.message || '创建托管机器人失败'
  } finally {
    isSubmitting.value = false
  }
}

function formatMoney(value: unknown) {
  const amount = Number(value ?? 0)
  if (!Number.isFinite(amount)) {
    return '--'
  }
  return amount.toLocaleString('zh-CN', { style: 'currency', currency: 'CNY', maximumFractionDigits: 2 })
}
</script>

<style scoped>
/* ── Modal Overlay — Bauhaus ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 310;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-md);
  background: var(--color-overlay);
}

.modal-card {
  width: min(680px, 100%);
  padding: var(--spacing-lg);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  box-shadow: var(--shadow-xl);
}

/* ── Header ── */
.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border-light);
}

.modal-eyebrow {
  margin: 0 0 4px;
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-accent);
}

.modal-title {
  margin: 0;
  font-size: var(--font-size-xxl);
  font-weight: 800;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.modal-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

/* ── Form ── */
.form-grid {
  display: grid;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.field {
  display: grid;
  gap: var(--spacing-sm);
}

.field__label {
  font-size: var(--font-size-xs);
  font-weight: 700;
  color: var(--color-text-secondary);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.field-control {
  min-height: 44px;
  padding: 0 var(--spacing-md);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-background);
  color: var(--color-text-primary);
  font-family: var(--font-family);
  font-size: var(--font-size-md);
  transition: border-color var(--transition-fast);
}

.field-control:focus {
  outline: none;
  border-color: var(--color-primary);
}

.field-control::placeholder {
  color: var(--color-text-muted);
}

/* ── Account Box ── */
.account-box {
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  background: var(--color-background);
  border: 1px solid var(--color-border-light);
}

.account-box__title {
  font-size: var(--font-size-xs);
  font-weight: 800;
  color: var(--color-text-muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: var(--spacing-sm);
}

.account-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.account-item {
  display: grid;
  gap: 2px;
}

.account-item__label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.account-item__value {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-text-primary);
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

/* ── Empty State ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xxl) var(--spacing-xl);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  text-align: center;
}

/* ── Footer ── */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border-light);
}

.btn-accent {
  min-height: 44px;
  padding: 0 var(--spacing-lg);
}

.btn-accent:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Error ── */
.error-text {
  margin: 0 0 var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  background: var(--color-danger-bg);
  color: var(--color-danger);
  font-size: var(--font-size-sm);
  font-weight: 600;
  border: 2px solid rgba(212, 57, 59, 0.25);
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .modal-card {
    padding: var(--spacing-md);
  }

  .modal-header {
    flex-direction: column;
  }

  .account-grid {
    grid-template-columns: 1fr;
  }

  .modal-footer {
    justify-content: stretch;
  }

  .modal-footer .btn {
    flex: 1;
  }
}
</style>
