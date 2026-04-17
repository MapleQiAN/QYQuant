<template>
  <div
    ref="dropdownRef"
    class="q-dropdown"
    :class="{ 'q-dropdown--open': isOpen }"
  >
    <div
      class="q-dropdown__trigger"
      @click="toggle"
    >
      <slot name="trigger" :isOpen="isOpen" />
    </div>

    <Transition name="q-dropdown-panel">
      <div
        v-if="isOpen"
        class="q-dropdown__panel"
        :class="[
          `q-dropdown__panel--${placement}`,
          { 'q-dropdown__panel--compact': compact }
        ]"
        :style="{ minWidth: minWidth || undefined }"
        role="menu"
        aria-orientation="vertical"
      >
        <slot name="header" />

        <template v-for="item in items" :key="item.key ?? item.label">
          <!-- Divider -->
          <div v-if="item.type === 'divider'" class="q-dropdown__divider" />

          <!-- Group label -->
          <div v-else-if="item.type === 'group'" class="q-dropdown__group-label">
            {{ item.label }}
          </div>

          <!-- Menu item -->
          <component
            v-else
            :is="item.to ? 'router-link' : 'button'"
            v-bind="item.to ? { to: item.to } : { type: 'button' }"
            class="q-dropdown__item"
            :class="{
              'q-dropdown__item--danger': item.danger,
              'q-dropdown__item--disabled': item.disabled,
              'q-dropdown__item--active': item.active
            }"
            :disabled="item.disabled"
            role="menuitem"
            @click="onItemClick(item)"
          >
            <span v-if="item.icon" class="q-dropdown__item-icon" v-html="item.icon" />
            <span class="q-dropdown__item-label">{{ item.label }}</span>
            <span v-if="item.shortcut" class="q-dropdown__item-shortcut">{{ item.shortcut }}</span>
          </component>
        </template>

        <slot name="footer" />
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

export interface DropdownItem {
  type?: 'item' | 'divider' | 'group'
  key?: string
  label?: string
  icon?: string
  shortcut?: string
  danger?: boolean
  disabled?: boolean
  active?: boolean
  to?: string
  action?: string
  [key: string]: unknown
}

withDefaults(defineProps<{
  items: DropdownItem[]
  placement?: 'bottom-start' | 'bottom-end' | 'top-start' | 'top-end'
  minWidth?: string
  compact?: boolean
}>(), {
  placement: 'bottom-end',
  compact: false,
})

const emit = defineEmits<{
  (e: 'select', item: DropdownItem): void
  (e: 'open'): void
  (e: 'close'): void
}>()

const dropdownRef = ref<HTMLElement | null>(null)
const isOpen = ref(false)

function toggle() {
  isOpen.value = !isOpen.value
  isOpen.value ? emit('open') : emit('close')
}

function open() {
  isOpen.value = true
  emit('open')
}

function close() {
  isOpen.value = false
  emit('close')
}

function onItemClick(item: DropdownItem) {
  if (item.disabled) return
  emit('select', item)
  if (item.type !== 'divider' && item.type !== 'group') {
    close()
  }
}

function handleClickOutside(e: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target as Node)) {
    if (isOpen.value) close()
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && isOpen.value) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside, true)
  document.addEventListener('keydown', handleKeydown)
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside, true)
  document.removeEventListener('keydown', handleKeydown)
})

defineExpose({ open, close, toggle })
</script>

<style scoped>
.q-dropdown {
  position: relative;
  display: inline-flex;
}

.q-dropdown__trigger {
  display: inline-flex;
  cursor: pointer;
}

/* ── Panel ── */
.q-dropdown__panel {
  position: absolute;
  z-index: 50;
  min-width: 180px;
  max-width: 320px;
  max-height: 360px;
  overflow-y: auto;
  padding: var(--spacing-xs);
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.q-dropdown__panel--bottom-start {
  top: calc(100% + 6px);
  left: 0;
}

.q-dropdown__panel--bottom-end {
  top: calc(100% + 6px);
  right: 0;
}

.q-dropdown__panel--top-start {
  bottom: calc(100% + 6px);
  left: 0;
}

.q-dropdown__panel--top-end {
  bottom: calc(100% + 6px);
  right: 0;
}

.q-dropdown__panel--compact {
  padding: 3px;
  border-radius: var(--radius-md);
}

/* Panel transition */
.q-dropdown-panel-enter-active {
  transition: opacity 0.15s ease, transform 0.2s var(--ease-out-expo);
}
.q-dropdown-panel-leave-active {
  transition: opacity 0.1s ease, transform 0.1s ease;
}
.q-dropdown-panel-enter-from,
.q-dropdown-panel-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.97);
}

/* ── Divider ── */
.q-dropdown__divider {
  height: 1px;
  margin: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-border-light);
}

/* ── Group Label ── */
.q-dropdown__group-label {
  padding: var(--spacing-sm) var(--spacing-md) var(--spacing-xs);
  font-size: 10px;
  font-weight: var(--font-weight-bold);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wider);
}

/* ── Item ── */
.q-dropdown__item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-decoration: none;
  text-align: left;
  transition: background var(--transition-fast), color var(--transition-fast);
  outline: none;
}

.q-dropdown__item:hover:not(.q-dropdown__item--disabled) {
  background: var(--color-surface-hover);
}

.q-dropdown__item:focus-visible {
  background: var(--color-surface-hover);
  box-shadow: inset 0 0 0 2px var(--color-primary);
}

.q-dropdown__item--active {
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

.q-dropdown__item--danger {
  color: var(--color-danger);
}

.q-dropdown__item--danger:hover {
  background: var(--color-danger-bg);
}

.q-dropdown__item--disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.q-dropdown__item-icon {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  color: var(--color-text-muted);
}

.q-dropdown__item--danger .q-dropdown__item-icon {
  color: var(--color-danger);
}

.q-dropdown__item-label {
  flex: 1;
}

.q-dropdown__item-shortcut {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--color-text-muted);
  padding: 1px 5px;
  background: var(--color-surface-elevated);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-xs);
}
</style>
