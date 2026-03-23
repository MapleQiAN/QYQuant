<template>
  <div class="modal-overlay">
    <div class="modal-card">
      <h2 class="modal-title">模拟托管免责声明</h2>
      <p class="modal-copy">{{ disclaimerText }}</p>

      <label class="checkbox-row">
        <input
          v-model="agreed"
          data-test="simulation-disclaimer-checkbox"
          type="checkbox"
        />
        <span>我已阅读并知晓上述风险提示</span>
      </label>

      <button
        :disabled="!agreed || isSubmitting"
        class="confirm-button"
        data-test="simulation-disclaimer-confirm"
        type="button"
        @click="confirm"
      >
        {{ isSubmitting ? '处理中...' : '确认' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { SIMULATION_DISCLAIMER } from '../../data/disclaimer-content'
import { useSimulationStore } from '../../stores/useSimulationStore'

const emit = defineEmits<{
  (event: 'accepted'): void
}>()

const simulationStore = useSimulationStore()
const disclaimerText = SIMULATION_DISCLAIMER
const agreed = ref(false)
const isSubmitting = ref(false)

async function confirm() {
  if (!agreed.value || isSubmitting.value) {
    return
  }

  isSubmitting.value = true
  try {
    await simulationStore.acceptDisclaimer()
    emit('accepted')
  } finally {
    isSubmitting.value = false
  }
}
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
  width: min(520px, 100%);
  padding: 24px;
  border-radius: 20px;
  background: var(--color-surface);
  box-shadow: var(--shadow-lg);
}

.modal-title {
  margin: 0 0 12px;
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.modal-copy {
  margin: 0 0 20px;
  line-height: 1.7;
  color: var(--color-text-secondary);
}

.checkbox-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-bottom: 20px;
  color: var(--color-text-secondary);
}

.confirm-button {
  min-width: 140px;
  min-height: 44px;
  padding: 0 18px;
  border: none;
  border-radius: 999px;
  background: #111827;
  color: #fff;
  cursor: pointer;
}

.confirm-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}
</style>
