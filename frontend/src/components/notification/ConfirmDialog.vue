<script setup lang="ts">
import { ref, onMounted } from 'vue'

export interface ConfirmProps {
  type?: 'success' | 'error' | 'warning' | 'info'
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  positive?: boolean
}

const props = withDefaults(defineProps<ConfirmProps>(), {
  type: 'warning',
  confirmText: '确认',
  cancelText: '取消',
  positive: false,
})

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

const overlayVisible = ref(false)

const typeConfig: Record<string, { icon: string; color: string }> = {
  success: {
    icon: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
    color: 'var(--color-success)',
  },
  error: {
    icon: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
    color: 'var(--color-danger)',
  },
  warning: {
    icon: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    color: 'var(--color-warning)',
  },
  info: {
    icon: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
    color: 'var(--color-info)',
  },
}

const config = typeConfig[props.type]

onMounted(() => {
  requestAnimationFrame(() => {
    overlayVisible.value = true
  })
})

function cancel() {
  overlayVisible.value = false
  setTimeout(() => emit('cancel'), 200)
}

function confirm() {
  overlayVisible.value = false
  setTimeout(() => emit('confirm'), 200)
}
</script>

<template>
  <div class="confirm-overlay" :class="{ visible: overlayVisible }" @click.self="cancel">
    <div class="confirm-dialog" :class="{ visible: overlayVisible }">
      <div class="confirm-header">
        <div class="confirm-icon" :style="{ color: config.color }" v-html="config.icon" />
        <span class="confirm-title">{{ title || '确认操作' }}</span>
      </div>
      <div class="confirm-body">
        <p class="confirm-message">{{ message }}</p>
      </div>
      <div class="confirm-actions">
        <button class="confirm-btn cancel-btn" @click="cancel">
          {{ cancelText }}
        </button>
        <button class="confirm-btn primary-btn" :class="{ danger: !positive }" @click="confirm">
          {{ confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  z-index: 10001;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0);
  transition: background 200ms ease;
}

.confirm-overlay.visible {
  background: var(--color-overlay);
}

.confirm-dialog {
  width: 420px;
  max-width: calc(100vw - 40px);
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  opacity: 0;
  transform: scale(0.92) translateY(10px);
  transition: all 240ms cubic-bezier(0.2, 0, 0, 1);
}

.confirm-dialog.visible {
  opacity: 1;
  transform: scale(1) translateY(0);
}

.confirm-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 24px 0;
}

.confirm-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.confirm-title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-text-primary);
}

.confirm-body {
  padding: 12px 24px 0;
}

.confirm-message {
  font-size: var(--font-size-md);
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
}

.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px 24px;
}

.confirm-btn {
  padding: 8px 20px;
  font-size: var(--font-size-md);
  font-weight: 600;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  font-family: var(--font-family);
  border: 2px solid var(--color-border);
}

.cancel-btn {
  background: var(--color-surface);
  color: var(--color-text-primary);
}

.cancel-btn:hover {
  background: var(--color-surface-hover);
}

.primary-btn {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-color: var(--color-primary);
}

.primary-btn:hover {
  opacity: 0.9;
}

.primary-btn.danger {
  background: var(--color-danger);
  border-color: var(--color-danger);
  color: var(--color-text-inverse);
}

.primary-btn.danger:hover {
  opacity: 0.9;
}
</style>
