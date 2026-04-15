<script setup lang="ts">
import { ref, onMounted } from 'vue'

export interface NotificationProps {
  id: string
  type?: 'success' | 'error' | 'warning' | 'info'
  title?: string
  message: string
  duration?: number
  closable?: boolean
}

const props = withDefaults(defineProps<NotificationProps>(), {
  type: 'info',
  duration: 3000,
  closable: true,
})

const emit = defineEmits<{ close: [id: string] }>()

const visible = ref(false)
let timer: ReturnType<typeof setTimeout> | null = null

const typeConfig: Record<string, { icon: string; color: string; bg: string }> = {
  success: {
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
    color: 'var(--color-success)',
    bg: 'var(--color-success-bg)',
  },
  error: {
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
    color: 'var(--color-danger)',
    bg: 'var(--color-danger-bg)',
  },
  warning: {
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    color: 'var(--color-warning)',
    bg: 'var(--color-warning-bg)',
  },
  info: {
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
    color: 'var(--color-info)',
    bg: 'var(--color-info-bg)',
  },
}

const config = typeConfig[props.type]

function close() {
  visible.value = false
  setTimeout(() => emit('close', props.id), 280)
}

function pauseTimer() {
  if (timer) {
    clearTimeout(timer)
    timer = null
  }
}

function resumeTimer() {
  if (props.duration > 0 && !timer) {
    timer = setTimeout(close, props.duration)
  }
}

onMounted(() => {
  requestAnimationFrame(() => {
    visible.value = true
  })
  if (props.duration > 0) {
    timer = setTimeout(close, props.duration)
  }
})
</script>

<template>
  <div
    class="notification-item"
    :class="[type, { visible }]"
    @mouseenter="pauseTimer"
    @mouseleave="resumeTimer"
    role="alert"
  >
    <div class="notification-accent" :style="{ backgroundColor: config.color }" />
    <div class="notification-icon" :style="{ color: config.color }" v-html="config.icon" />
    <div class="notification-body">
      <span v-if="title" class="notification-title">{{ title }}</span>
      <span class="notification-message">{{ message }}</span>
    </div>
    <button v-if="closable" class="notification-close" @click="close" aria-label="Close">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  position: relative;
  width: 360px;
  max-width: calc(100vw - 40px);
  padding: 14px 16px;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  opacity: 0;
  transform: translateX(40px) scale(0.96);
  transition: all 280ms cubic-bezier(0.2, 0, 0, 1);
  pointer-events: auto;
  overflow: hidden;
}

.notification-item.visible {
  opacity: 1;
  transform: translateX(0) scale(1);
}

.notification-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  border-radius: 2px 0 0 2px;
}

.notification-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  margin-left: 4px;
}

.notification-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.notification-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.4;
}

.notification-message {
  font-size: var(--font-size-md);
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.notification-close {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  color: var(--color-text-muted);
  cursor: pointer;
  border-radius: var(--radius-xs);
  transition: all var(--transition-fast);
  margin: -2px -4px -2px 0;
}

.notification-close:hover {
  color: var(--color-text-primary);
  background: var(--color-surface-hover);
}
</style>
