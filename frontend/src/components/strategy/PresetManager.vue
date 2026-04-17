<template>
  <section class="preset-manager">
    <div class="preset-toolbar">
      <QSelect
        data-test="preset-select"
        :model-value="selectedPresetId"
        :options="presetOptions"
        :placeholder="t('strategy.presets.loadPreset')"
        @update:model-value="emit('select', $event)"
      />

      <div class="preset-actions">
        <button
          data-test="open-save-preset"
          class="btn btn-secondary"
          type="button"
          :disabled="saving"
          @click="dialogOpen = true"
        >
          {{ t('strategy.presets.savePreset') }}
        </button>
        <button
          data-test="delete-preset"
          class="btn btn-secondary danger"
          type="button"
          :disabled="deleting || !selectedPresetId"
          @click="emit('delete', selectedPresetId)"
        >
          {{ t('strategy.presets.deletePreset') }}
        </button>
      </div>
    </div>

    <Transition name="dialog">
      <div v-if="dialogOpen" class="dialog-backdrop" @click.self="closeDialog">
        <div class="dialog-panel">
          <h3 class="dialog-title">{{ t('strategy.presets.savePreset') }}</h3>
          <input
            data-test="preset-name-input"
            v-model.trim="presetName"
            class="preset-input"
            type="text"
            :placeholder="t('strategy.presets.presetNamePlaceholder')"
            @keydown.enter="confirmSave"
          />
          <div class="dialog-actions">
            <button class="btn btn-secondary" type="button" @click="closeDialog">{{ t('common.cancel') }}</button>
            <button
              data-test="confirm-save-preset"
              class="btn btn-primary"
              type="button"
              :disabled="!presetName"
              @click="confirmSave"
            >
              {{ t('common.save') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { StrategyPreset } from '../../types/Strategy'
import { QSelect } from '../ui'

const { t } = useI18n()

const props = defineProps<{
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

const presetOptions = computed(() =>
  props.presets.map((p) => ({ label: p.name, value: p.id }))
)

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
  border: 2px solid var(--color-border);
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-family: var(--font-mono);
  transition: border-color 0.15s;
}

.preset-select:focus,
.preset-input:focus {
  outline: none;
  border-color: var(--color-primary-border);
  box-shadow: 0 0 0 3px rgba(30, 90, 168, 0.12);
}

.preset-actions {
  display: flex;
  gap: var(--spacing-sm);
}

/* ── Dialog ── */
.dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: var(--color-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
}

.dialog-panel {
  width: min(100%, 380px);
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  box-shadow: var(--shadow-xl);
}

.dialog-title {
  margin: 0 0 var(--spacing-md);
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-text-primary);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
}

.danger {
  color: var(--color-danger);
  border-color: var(--color-danger);
}

/* ── Dialog Transition ── */
.dialog-enter-active {
  transition: opacity 0.2s ease;
}
.dialog-enter-active .dialog-panel {
  transition: opacity 0.2s ease, transform 0.2s var(--ease-out-expo, ease);
}
.dialog-leave-active {
  transition: opacity 0.15s ease;
}
.dialog-leave-active .dialog-panel {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dialog-enter-from {
  opacity: 0;
}
.dialog-enter-from .dialog-panel {
  opacity: 0;
  transform: scale(0.96) translateY(8px);
}
.dialog-leave-to {
  opacity: 0;
}
.dialog-leave-to .dialog-panel {
  opacity: 0;
  transform: scale(0.96);
}
</style>
