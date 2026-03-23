<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="detail-modal">
      <div class="detail-modal__header">
        <div>
          <h2 class="detail-modal__title">{{ bot.strategy_name }}</h2>
          <p class="detail-modal__subtitle">模拟收益与买卖信号</p>
        </div>
        <div class="detail-modal__header-actions">
          <span class="detail-modal__badge" :class="`detail-modal__badge--${bot.status}`">{{ statusLabel }}</span>
          <button class="detail-modal__close" type="button" aria-label="关闭" @click="emit('close')">×</button>
        </div>
      </div>

      <section class="detail-section">
        <div class="detail-section__header">
          <h3 class="detail-section__title">收益曲线</h3>
        </div>
        <div v-if="isLoading" class="detail-section__loading">加载中...</div>
        <SimulationChart v-else :records="records" />
      </section>

      <section class="detail-section">
        <div class="detail-section__header">
          <h3 class="detail-section__title">买卖信号记录</h3>
        </div>
        <div v-if="isLoading" class="detail-section__loading">加载中...</div>
        <div v-else-if="trades.length === 0" class="detail-section__empty">暂无买卖记录</div>
        <table v-else class="trades-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>标的</th>
              <th>方向</th>
              <th>价格</th>
              <th>数量</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="trade in trades" :key="`${trade.trade_date}-${trade.symbol}-${trade.side}-${trade.price}`">
              <td>{{ trade.trade_date }}</td>
              <td>{{ trade.symbol }}</td>
              <td :class="trade.side === 'buy' ? 'trade-side trade-side--buy' : 'trade-side trade-side--sell'">
                {{ trade.side === 'buy' ? '买入' : '卖出' }}
              </td>
              <td>¥ {{ trade.price }}</td>
              <td>{{ trade.quantity }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { createBotStream, getSimRecords, getSimTrades } from '../../api/simulation'
import { useUserStore } from '../../stores/user'
import type { SimBotStreamPayload, SimulationBot, SimulationRecord, SimulationTrade } from '../../types/Simulation'
import SimulationChart from './SimulationChart.vue'

const props = defineProps<{ bot: SimulationBot }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const records = ref<SimulationRecord[]>([])
const trades = ref<SimulationTrade[]>([])
const isLoading = ref(false)
let eventSource: Pick<EventSource, 'close'> | null = null

const statusLabel = computed(() => ({
  active: '运行中',
  paused: '已暂停',
  stopped: '已停止',
}[props.bot.status] ?? props.bot.status))

function mergeStreamRecords(streamRecords: SimBotStreamPayload['records']): SimulationRecord[] {
  const existingCashByDate = new Map(records.value.map((record) => [record.trade_date, record.cash]))
  return streamRecords.map((record) => ({
    trade_date: record.trade_date,
    equity: record.equity,
    cash: existingCashByDate.get(record.trade_date) ?? '0.00',
    daily_return: record.daily_return,
  }))
}

onMounted(async () => {
  isLoading.value = true
  try {
    const [nextRecords, nextTrades] = await Promise.all([
      getSimRecords(props.bot.id),
      getSimTrades(props.bot.id),
    ])
    records.value = nextRecords
    trades.value = nextTrades
  } finally {
    isLoading.value = false
  }

  const userStore = useUserStore()
  const token = userStore.token
  if (!token) {
    return
  }

  eventSource = createBotStream(props.bot.id, token, (payload) => {
    records.value = mergeStreamRecords(payload.records)
  })
})

onUnmounted(() => {
  eventSource?.close()
  eventSource = null
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 110;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.45);
}

.detail-modal {
  width: min(1080px, 100%);
  max-height: 88vh;
  overflow-y: auto;
  border-radius: 24px;
  background: #fff;
  padding: 24px;
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.25);
}

.detail-modal__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
}

.detail-modal__title {
  margin: 0;
  font-size: 24px;
  color: var(--color-text-primary);
}

.detail-modal__subtitle {
  margin: 6px 0 0;
  color: var(--color-text-muted);
}

.detail-modal__header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-modal__badge {
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.detail-modal__badge--active {
  background: #d1fae5;
  color: #065f46;
}

.detail-modal__badge--paused {
  background: #fef3c7;
  color: #92400e;
}

.detail-modal__badge--stopped {
  background: #fee2e2;
  color: #991b1b;
}

.detail-modal__close {
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 24px;
  cursor: pointer;
}

.detail-section + .detail-section {
  margin-top: 24px;
}

.detail-section__header {
  margin-bottom: 12px;
}

.detail-section__title {
  margin: 0;
  font-size: 18px;
  color: var(--color-text-primary);
}

.detail-section__loading,
.detail-section__empty {
  padding: 24px 0;
  text-align: center;
  color: var(--color-text-muted);
}

.trades-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.trades-table th,
.trades-table td {
  padding: 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  text-align: left;
}

.trade-side {
  font-weight: 600;
}

.trade-side--buy {
  color: #047857;
}

.trade-side--sell {
  color: #b91c1c;
}

@media (max-width: 768px) {
  .modal-overlay {
    padding: 12px;
  }

  .detail-modal {
    padding: 18px;
  }

  .detail-modal__header {
    flex-direction: column;
  }

  .trades-table {
    font-size: 13px;
  }
}
</style>
