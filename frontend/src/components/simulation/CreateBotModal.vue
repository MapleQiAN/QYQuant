<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card">
      <div class="header-row">
        <h2 class="modal-title">创建模拟机器人</h2>
        <button class="ghost-button" type="button" @click="$emit('close')">关闭</button>
      </div>

      <div class="form-grid">
        <label class="field">
          <span>策略</span>
          <select v-model="strategyId" class="field-control">
            <option disabled value="">请选择策略</option>
            <option
              v-for="strategy in strategiesStore.library"
              :key="strategy.id"
              :value="strategy.id"
            >
              {{ strategy.title || strategy.name }}
            </option>
          </select>
        </label>

        <label class="field">
          <span>初始资金</span>
          <input
            v-model.number="initialCapital"
            class="field-control"
            min="1000"
            step="1"
            type="number"
          />
        </label>
      </div>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <p v-if="showUpgradeHint" class="hint-text">
        当前套餐已达模拟机器人上限，请升级套餐。
      </p>

      <div class="footer-row">
        <button
          :disabled="isSubmitting || !strategyId || initialCapital < 1000"
          class="primary-button"
          type="button"
          @click="submit"
        >
          {{ isSubmitting ? '创建中...' : '创建机器人' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useSimulationStore } from '../../stores/useSimulationStore'
import { useStrategiesStore } from '../../stores/strategies'

const emit = defineEmits<{
  (event: 'close'): void
  (event: 'created'): void
}>()

const simulationStore = useSimulationStore()
const strategiesStore = useStrategiesStore()

const strategyId = ref('')
const initialCapital = ref(100000)
const isSubmitting = ref(false)
const errorMessage = ref('')

const showUpgradeHint = computed(() => simulationStore.errorCode === 'SIMULATION_SLOT_LIMIT_REACHED')

onMounted(async () => {
  if (!strategiesStore.library.length) {
    await strategiesStore.loadLibrary({ page: 1, perPage: 100 })
  }
})

async function submit() {
  if (!strategyId.value || initialCapital.value < 1000 || isSubmitting.value) {
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''
  try {
    await simulationStore.createBot({
      strategy_id: strategyId.value,
      initial_capital: initialCapital.value,
    })
    emit('created')
  } catch (error: any) {
    errorMessage.value = error?.message || '创建模拟机器人失败'
  } finally {
    isSubmitting.value = false
  }
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
  background: rgba(15, 23, 42, 0.35);
}

.modal-card {
  width: min(560px, 100%);
  padding: 24px;
  border-radius: 20px;
  background: var(--color-surface);
  box-shadow: var(--shadow-lg);
}

.header-row,
.footer-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-title {
  margin: 0;
  font-size: var(--font-size-xl);
}

.form-grid {
  display: grid;
  gap: 16px;
  margin: 20px 0 16px;
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
  margin: 0 0 8px;
  color: #b91c1c;
}

.hint-text {
  margin: 0 0 12px;
  color: #92400e;
}
</style>
