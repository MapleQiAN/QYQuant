<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card">
      <div class="header-row">
        <h2 class="modal-title">机器人持仓</h2>
        <button class="ghost-button" type="button" @click="$emit('close')">关闭</button>
      </div>

      <div v-if="isLoading" class="empty-state">加载中...</div>
      <div v-else-if="positions.length === 0" class="empty-state">暂无持仓（机器人尚未产生持仓）。</div>
      <table v-else class="positions-table">
        <thead>
          <tr>
            <th>标的</th>
            <th>数量</th>
            <th>成本价</th>
            <th>市值</th>
            <th>已实现收益</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="position in positions" :key="position.symbol">
            <td>{{ position.symbol }}</td>
            <td>{{ position.quantity }}</td>
            <td>{{ position.avgCost }}</td>
            <td>{{ position.marketValue }}</td>
            <td>{{ position.realizedPnl }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useBotsStore } from '../../stores/bots'

const props = defineProps<{ botId: string }>()
defineEmits<{ (e: 'close'): void }>()

const botsStore = useBotsStore()
const isLoading = ref(false)
const positions = computed(() => botsStore.positionsById[props.botId] ?? [])

onMounted(async () => {
  isLoading.value = true
  try {
    await botsStore.loadPositions(props.botId)
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 320;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(15, 23, 42, 0.45);
}

.modal-card {
  width: min(880px, 100%);
  max-height: 80vh;
  overflow: auto;
  padding: 24px;
  border-radius: 24px;
  background: #fff;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.modal-title {
  margin: 0;
  font-size: 22px;
}

.ghost-button {
  min-height: 40px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: transparent;
}

.empty-state {
  padding: 32px 0;
  text-align: center;
  color: var(--color-text-muted);
}

.positions-table {
  width: 100%;
  border-collapse: collapse;
}

.positions-table th,
.positions-table td {
  padding: 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  text-align: left;
}
</style>
