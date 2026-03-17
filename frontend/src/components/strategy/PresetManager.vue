<template>
  <section class="preset-manager">
    <div class="preset-toolbar">
      <select
        data-test="preset-select"
        class="preset-select"
        :value="selectedPresetId"
        @change="emit('select', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">选择预设</option>
        <option v-for="preset in presets" :key="preset.id" :value="preset.id">
          {{ preset.name }}
        </option>
      </select>

      <div class="preset-actions">
        <button
          data-test="open-save-preset"
          class="btn btn-secondary"
          type="button"
          :disabled="saving"
          @click="dialogOpen = true"
        >
          保存为预设
        </button>
        <button
          data-test="delete-preset"
          class="btn btn-secondary danger"
          type="button"
          :disabled="deleting || !selectedPresetId"
          @click="emit('delete', selectedPresetId)"
        >
          删除预设
        </button>
      </div>
    </div>

    <div v-if="dialogOpen" class="dialog-backdrop">
      <div class="dialog-panel">
        <h3 class="dialog-title">保存预设</h3>
        <input
          data-test="preset-name-input"
          v-model.trim="presetName"
          class="preset-input"
          type="text"
          placeholder="输入预设名称"
        />
        <div class="dialog-actions">
          <button class="btn btn-secondary" type="button" @click="closeDialog">取消</button>
          <button
            data-test="confirm-save-preset"
            class="btn btn-primary"
            type="button"
            :disabled="!presetName"
            @click="confirmSave"
          >
            保存
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { StrategyPreset } from '../../types/Strategy'

defineProps<{
  presets: StrategyPreset[]
  selectedPresetId: string
  saving?: boolean
  deleting?: boolean
}>()

const emit = defineEmits<{
  (event: 'select', presetId: string): void
  (event: 'save', name: string): void
  (event: 'delete', presetId: string): void
}>()

const dialogOpen = ref(false)
const presetName = ref('')

function closeDialog() {
  dialogOpen.value = false
  presetName.value = ''
}

function confirmSave() {
  if (!presetName.value) {
    return
  }
  emit('save', presetName.value)
  closeDialog()
}
</script>

<style scoped>
.preset-manager {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.preset-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  align-items: center;
  justify-content: space-between;
}

.preset-select,
.preset-input {
  min-width: 220px;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-primary);
}

.preset-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.dialog-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.32);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
}

.dialog-panel {
  width: min(100%, 360px);
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  box-shadow: var(--shadow-lg);
}

.dialog-title {
  margin: 0 0 var(--spacing-md);
  color: var(--color-text-primary);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.danger {
  color: var(--color-danger);
}
</style>
