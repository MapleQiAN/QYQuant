<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card">
      <div class="header-row">
        <div>
          <h2 class="modal-title">创建量化托管机器人</h2>
          <p class="modal-subtitle">选择你的策略、券商账户和托管金额，生成一个真实托管机器人。</p>
        </div>
        <button class="ghost-button" type="button" @click="$emit('close')">关闭</button>
      </div>

      <div v-if="brokerOptions.length === 0" class="empty-state">
        <p>暂无可用券商连接。请先在设置页绑定券商 API 账户。</p>
      </div>

      <template v-else>
        <div class="form-grid">
          <label class="field">
            <span>机器人名称</span>
            <input v-model="name" class="field-control" maxlength="64" placeholder="例如：沪深择时一号" type="text" />
          </label>

          <label class="field">
            <span>策略</span>
            <QSelect
              v-model="strategyId"
              :options="strategyOptions"
              placeholder="选择策略"
              searchable
            />
          </label>

          <label class="field">
            <span>券商账户</span>
            <QSelect
              v-model="integrationId"
              :options="brokerOptions"
              placeholder="选择券商账户"
              searchable
            />
          </label>

          <label class="field">
            <span>托管金额</span>
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
          <strong>账户概览</strong>
          <div class="account-grid">
            <div class="account-item">
              <span>可用资金</span>
              <strong>{{ formatMoney(accountSummary.available_cash ?? accountSummary.available ?? accountSummary.cash) }}</strong>
            </div>
            <div class="account-item">
              <span>账户权益</span>
              <strong>{{ formatMoney(accountSummary.equity) }}</strong>
            </div>
          </div>
        </div>

        <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

        <div class="footer-row">
          <button
            :disabled="isSubmitting || !strategyId || !integrationId || capital < 1000"
            class="primary-button"
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
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 310;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(15, 23, 42, 0.45);
}

.modal-card {
  width: min(680px, 100%);
  padding: 24px;
  border-radius: 24px;
  background: var(--color-surface);
  box-shadow: var(--shadow-lg);
}

.header-row,
.footer-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.modal-title {
  margin: 0;
  font-size: 24px;
}

.modal-subtitle {
  margin: 8px 0 0;
  color: var(--color-text-muted);
}

.form-grid {
  display: grid;
  gap: 16px;
  margin: 24px 0 16px;
}

.field {
  display: grid;
  gap: 8px;
  color: var(--color-text-secondary);
}

.field-control {
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 12px;
  background: #fff;
}

.account-box,
.empty-state {
  margin: 0 0 16px;
  padding: 16px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.04);
  color: var(--color-text-secondary);
}

.account-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.account-item {
  display: grid;
  gap: 4px;
}

.primary-button,
.ghost-button {
  min-height: 44px;
  padding: 0 18px;
  border-radius: 999px;
  cursor: pointer;
}

.primary-button {
  border: none;
  background: #111827;
  color: #fff;
}

.primary-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.ghost-button {
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: transparent;
}

.error-text {
  margin: 0 0 12px;
  color: #b91c1c;
}

@media (max-width: 768px) {
  .modal-card {
    padding: 18px;
  }

  .header-row,
  .footer-row {
    flex-direction: column;
  }

  .account-grid {
    grid-template-columns: 1fr;
  }
}
</style>
