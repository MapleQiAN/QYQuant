<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card">
      <div class="header-row">
        <div>
          <h2 class="modal-title">{{ bot.name }}</h2>
          <p class="modal-subtitle">{{ bot.strategyName }} · {{ bot.integrationDisplayName }}</p>
        </div>
        <button class="ghost-button" type="button" @click="$emit('close')">关闭</button>
      </div>

      <div class="summary-grid">
        <div class="summary-item">
          <span>最新权益</span>
          <strong>{{ formatMoney(summary.latestEquity) }}</strong>
        </div>
        <div class="summary-item">
          <span>总收益</span>
          <strong :class="summary.totalProfit >= 0 ? 'up' : 'down'">{{ formatMoney(summary.totalProfit) }}</strong>
        </div>
        <div class="summary-item">
          <span>收益率</span>
          <strong :class="summary.totalReturnRate >= 0 ? 'up' : 'down'">{{ (summary.totalReturnRate * 100).toFixed(2) }}%</strong>
        </div>
      </div>

      <section class="detail-section">
        <div class="detail-section__header">
          <h3 class="detail-section__title">盈利曲线</h3>
        </div>
        <div v-if="isLoading" class="detail-section__empty">加载中...</div>
        <SimulationChart v-else :records="chartRecords" />
      </section>

      <section class="detail-section">
        <div class="detail-section__header">
          <h3 class="detail-section__title">执行订单</h3>
        </div>
        <div v-if="isLoading" class="detail-section__empty">加载中...</div>
        <div v-else-if="orders.length === 0" class="detail-section__empty">暂无机器人订单记录</div>
        <table v-else class="orders-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>标的</th>
              <th>方向</th>
              <th>价格</th>
              <th>数量</th>
              <th>PnL</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in orders" :key="order.id">
              <td>{{ formatTimestamp(order.timestamp) }}</td>
              <td>{{ order.symbol }}</td>
              <td>{{ order.side }}</td>
              <td>{{ order.price }}</td>
              <td>{{ order.quantity }}</td>
              <td>{{ order.pnl ?? '--' }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useBotsStore } from '../../stores/bots'
import type { ManagedBot } from '../../types/Bot'
import SimulationChart from '../simulation/SimulationChart.vue'

const props = defineProps<{ bot: ManagedBot }>()
defineEmits<{ (e: 'close'): void }>()

const botsStore = useBotsStore()
const isLoading = ref(false)

const performance = computed(() => botsStore.performanceById[props.bot.id])
const summary = computed(() => performance.value?.summary ?? {
  latestEquity: props.bot.capital,
  totalProfit: props.bot.profit,
  totalReturnRate: props.bot.totalReturnRate,
})
const orders = computed(() => performance.value?.orders ?? [])
const chartRecords = computed(() =>
  (performance.value?.equityCurve ?? []).map((point) => ({
    trade_date: point.snapshotDate,
    equity: point.equity.toFixed(2),
    cash: point.availableCash.toFixed(2),
    daily_return: point.totalReturnRate.toFixed(6),
  }))
)

onMounted(async () => {
  isLoading.value = true
  try {
    await botsStore.loadPerformance(props.bot.id)
  } finally {
    isLoading.value = false
  }
})

function formatMoney(value: number) {
  return value.toLocaleString('zh-CN', { style: 'currency', currency: 'CNY', maximumFractionDigits: 2 })
}

function formatTimestamp(value: number) {
  if (!value) {
    return '--'
  }
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 315;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(15, 23, 42, 0.45);
}

.modal-card {
  width: min(1080px, 100%);
  max-height: 88vh;
  overflow-y: auto;
  border-radius: 24px;
  background: #fff;
  padding: 24px;
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.25);
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
}

.modal-title {
  margin: 0;
  font-size: 24px;
}

.modal-subtitle {
  margin: 6px 0 0;
  color: var(--color-text-muted);
}

.ghost-button {
  min-height: 40px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: transparent;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.summary-item {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.04);
}

.summary-item span {
  color: var(--color-text-muted);
}

.summary-item strong {
  font-size: 18px;
}

.up {
  color: #047857;
}

.down {
  color: #b91c1c;
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
}

.detail-section__empty {
  padding: 24px 0;
  text-align: center;
  color: var(--color-text-muted);
}

.orders-table {
  width: 100%;
  border-collapse: collapse;
}

.orders-table th,
.orders-table td {
  padding: 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  text-align: left;
}

@media (max-width: 768px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
