<template>
  <Teleport to="body">
    <div
      v-if="props.modelValue"
      class="simulation-disclaimer-root"
      data-test="simulation-disclaimer-overlay"
      @click.stop
    >
      <div class="simulation-disclaimer-backdrop" />
      <div
        ref="dialogRef"
        aria-labelledby="simulation-disclaimer-title"
        aria-modal="true"
        class="simulation-disclaimer-dialog"
        data-test="simulation-disclaimer-dialog"
        role="alertdialog"
        @keydown="handleKeydown"
      >
        <button
          ref="closeButtonRef"
          aria-label="关闭风险提示"
          class="close-button"
          data-test="simulation-disclaimer-close"
          type="button"
          @click="close"
        >
          ×
        </button>

        <h2 id="simulation-disclaimer-title" class="dialog-title">风险提示</h2>
        <p class="dialog-copy">{{ props.text }}</p>

        <label class="dialog-checkbox">
          <input
            v-model="acknowledged"
            class="dialog-checkbox-input"
            data-test="simulation-disclaimer-checkbox"
            type="checkbox"
          />
          <span>我已知晓以上风险</span>
        </label>

        <button
          :disabled="!acknowledged"
          class="confirm-button"
          data-test="simulation-disclaimer-confirm"
          type="button"
          @click="confirm"
        >
          确认
        </button>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { SIMULATION_DISCLAIMER } from '../../data/disclaimer-content'

const SIMULATION_DISCLAIMER_STORAGE_KEY = 'qyquant.simulation-disclaimer-accepted'

const props = withDefaults(defineProps<{
  modelValue: boolean
  text?: string
  storageKey?: string
}>(), {
  text: SIMULATION_DISCLAIMER,
  storageKey: SIMULATION_DISCLAIMER_STORAGE_KEY,
})

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'confirm'): void
}>()

const acknowledged = ref(false)
const dialogRef = ref<HTMLElement | null>(null)
const closeButtonRef = ref<HTMLButtonElement | null>(null)
let previousActiveElement: HTMLElement | null = null

watch(
  () => props.modelValue,
  async (open) => {
    if (open) {
      acknowledged.value = false
      previousActiveElement = document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null
      await nextTick()
      closeButtonRef.value?.focus()
      return
    }

    restoreFocus()
  },
  { immediate: true },
)

function restoreFocus() {
  previousActiveElement?.focus?.()
}

function close() {
  restoreFocus()
  emit('update:modelValue', false)
}

function confirm() {
  if (!acknowledged.value) {
    return
  }

  window.localStorage.setItem(props.storageKey, 'true')
  emit('confirm')
  close()
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.preventDefault()
    close()
    return
  }

  if (event.key !== 'Tab') {
    return
  }

  const focusable = getFocusableElements()
  if (!focusable.length) {
    return
  }

  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  const active = document.activeElement

  if (event.shiftKey && active === first) {
    event.preventDefault()
    last.focus()
    return
  }

  if (!event.shiftKey && active === last) {
    event.preventDefault()
    first.focus()
  }
}

function getFocusableElements() {
  const root = dialogRef.value
  if (!root) {
    return []
  }

  return Array.from(
    root.querySelectorAll<HTMLElement>(
      'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  )
}
</script>

<style scoped>
.simulation-disclaimer-root {
  position: fixed;
  inset: 0;
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.simulation-disclaimer-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
}

.simulation-disclaimer-dialog {
  position: relative;
  z-index: 1;
  width: min(480px, calc(100vw - 32px));
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-lg);
}

.close-button {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
}

.close-button:focus-visible,
.dialog-checkbox-input:focus-visible,
.confirm-button:focus-visible {
  outline: 2px solid #e53935;
  outline-offset: 2px;
}

.dialog-title {
  margin: 0 0 var(--spacing-sm);
  font-size: var(--font-size-xl);
}

.dialog-copy {
  margin: 0 0 var(--spacing-lg);
  color: var(--color-text-secondary);
}

.dialog-checkbox {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
  color: var(--color-text-secondary);
}

.dialog-checkbox-input {
  width: 18px;
  height: 18px;
}

.confirm-button {
  min-width: 120px;
  min-height: 44px;
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  border-radius: var(--radius-md);
  background: #1a1a1a;
  color: var(--color-text-inverse);
  cursor: pointer;
}

.confirm-button:disabled {
  background: var(--color-text-muted);
  cursor: not-allowed;
}
</style>
