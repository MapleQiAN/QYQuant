<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h2 class="modal-title">当前持仓</h2>
        <button class="modal-close" type="button" aria-label="关闭" @click="emit('close')">✕</button>
      </div>

      <div v-if="isLoading" class="modal-loading">加载中...</div>

      <p v-else-if="positions.length === 0" class="modal-empty">
        暂无持仓（机器人尚未执行过模拟交易）
      </p>

      <table v-else class="positions-table">
        <thead>
          <tr>
            <th>标的代码</th>
            <th>持仓数量</th>
            <th>平均成本</th>
            <th>更新时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pos in positions" :key="pos.symbol">
            <td>{{ pos.symbol }}</td>
            <td>{{ pos.quantity }}</td>
            <td>¥ {{ pos.avg_cost }}</td>
            <td>{{ pos.updated_at.slice(0, 10) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useSimulationStore } from '../../stores/useSimulationStore'
import type { SimulationPosition } from '../../types/Simulation'

const props = defineProps<{ botId: string }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const simulationStore = useSimulationStore()
const positions = ref<SimulationPosition[]>([])
const isLoading = ref(false)

onMounted(async () => {
  isLoading.value = true
  try {
    positions.value = await simulationStore.fetchPositions(props.botId)
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-content {
  width: min(560px, 90vw);
  max-height: 80vh;
  overflow-y: auto;
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.modal-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: var(--color-text-muted);
  padding: 4px;
}

.modal-loading,
.modal-empty {
  text-align: center;
  color: var(--color-text-muted);
  padding: 24px 0;
}

.positions-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.positions-table th {
  text-align: left;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.3);
  color: var(--color-text-muted);
  font-weight: 500;
}

.positions-table td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.15);
  color: var(--color-text-primary);
}

.positions-table tbody tr:last-child td {
  border-bottom: none;
}
</style>
