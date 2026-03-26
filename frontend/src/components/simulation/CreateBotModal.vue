<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card">
      <div class="header-row">
        <h2 class="modal-title">Create Simulation Bot</h2>
        <button class="ghost-button" type="button" @click="$emit('close')">Close</button>
      </div>

      <div class="form-grid">
        <label class="field">
          <span>Strategy</span>
          <select v-model="strategyId" class="field-control">
            <option disabled value="">Select a strategy</option>
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
          <span>Initial Capital</span>
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
        Your current plan has reached the simulation bot limit. Upgrade your plan to create more bots.
      </p>

      <div class="footer-row">
        <button
          :disabled="isSubmitting || !strategyId || initialCapital < 1000"
          class="primary-button"
          type="button"
          @click="submit"
        >
          {{ isSubmitting ? 'Creating...' : 'Create Bot' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useSimulationStore } from '../../stores/useSimulationStore'
import { useStrategiesStore } from '../../stores/strategies'

const props = withDefaults(defineProps<{
  initialStrategyId?: string
}>(), {
  initialStrategyId: ''
})

const emit = defineEmits<{
  (event: 'close'): void
  (event: 'created'): void
}>()

const simulationStore = useSimulationStore()
const strategiesStore = useStrategiesStore()

const strategyId = ref(props.initialStrategyId)
const initialCapital = ref(100000)
const isSubmitting = ref(false)
const errorMessage = ref('')

const showUpgradeHint = computed(() => simulationStore.errorCode === 'SIMULATION_SLOT_LIMIT_REACHED')

onMounted(async () => {
  if (!strategiesStore.library.length) {
    await strategiesStore.loadLibrary({ page: 1, perPage: 100 })
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
    errorMessage.value = error?.message || 'Failed to create simulation bot'
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
