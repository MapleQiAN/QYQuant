<template>
  <div
    ref="selectRef"
    class="q-select"
    :class="[
      `q-select--${size}`,
      { 'q-select--open': isOpen, 'q-select--disabled': disabled, 'q-select--invalid': invalid }
    ]"
  >
    <button
      ref="triggerRef"
      type="button"
      class="q-select__trigger"
      :disabled="disabled"
      :aria-expanded="isOpen"
      :aria-haspopup="'listbox'"
      :aria-labelledby="labelId"
      @click="toggle"
      @keydown="onTriggerKeydown"
    >
      <span v-if="selectedLabel" class="q-select__value">{{ selectedLabel }}</span>
      <span v-else class="q-select__placeholder">{{ placeholder }}</span>

      <svg class="q-select__chevron" :class="{ 'q-select__chevron--open': isOpen }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="6 9 12 15 18 9" />
      </svg>
    </button>

    <Teleport to="body">
      <Transition name="q-select-panel">
        <div ref="panelRef" v-if="isOpen" class="q-select__panel" :style="panelStyle">
        <div v-if="searchable" class="q-select__search-wrap">
          <svg class="q-select__search-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            ref="searchRef"
            v-model="searchQuery"
            class="q-select__search"
            type="text"
            :placeholder="searchPlaceholder"
            @keydown="onSearchKeydown"
          />
        </div>

        <ul class="q-select__options" role="listbox" :aria-activedescendant="activeDescendant">
          <li
            v-for="(option, index) in filteredOptions"
            :id="`${id}-option-${index}`"
            :key="getOptionKey(option)"
            class="q-select__option"
            :class="{
              'q-select__option--active': index === activeIndex,
              'q-select__option--selected': isOptionSelected(option),
              'q-select__option--disabled': option.disabled
            }"
            role="option"
            :aria-selected="isOptionSelected(option)"
            @click="selectOption(option)"
            @mouseenter="activeIndex = index"
          >
            <slot name="option" :option="option" :selected="isOptionSelected(option)">
              <span class="q-select__option-label">{{ getOptionLabel(option) }}</span>
            </slot>

            <svg v-if="isOptionSelected(option)" class="q-select__check" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </li>

          <li v-if="filteredOptions.length === 0" class="q-select__empty">
            {{ emptyText }}
          </li>
        </ul>
      </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

export interface SelectOption {
  label: string
  value: unknown
  disabled?: boolean
  [key: string]: unknown
}

const props = withDefaults(defineProps<{
  options: SelectOption[]
  modelValue: unknown
  placeholder?: string
  disabled?: boolean
  searchable?: boolean
  searchPlaceholder?: string
  emptyText?: string
  size?: 'sm' | 'md' | 'lg'
  invalid?: boolean
  placement?: 'bottom' | 'top'
}>(), {
  placeholder: 'Select...',
  disabled: false,
  searchable: false,
  searchPlaceholder: 'Search...',
  emptyText: 'No results',
  size: 'md',
  invalid: false,
  placement: 'bottom',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: unknown): void
  (e: 'change', value: unknown): void
}>()

const id = `q-select-${Math.random().toString(36).slice(2, 9)}`
const labelId = `${id}-label`

const selectRef = ref<HTMLElement | null>(null)
const triggerRef = ref<HTMLButtonElement | null>(null)
const searchRef = ref<HTMLInputElement | null>(null)
const panelRef = ref<HTMLElement | null>(null)
const isOpen = ref(false)
const searchQuery = ref('')
const activeIndex = ref(-1)
const positionTick = ref(0)

function updatePosition() {
  if (isOpen.value) positionTick.value++
}
function onScroll() { updatePosition() }
function onResize() { updatePosition() }

const filteredOptions = computed(() => {
  if (!searchQuery.value) return props.options
  const q = searchQuery.value.toLowerCase()
  return props.options.filter(o => getOptionLabel(o).toLowerCase().includes(q))
})

const selectedLabel = computed(() => {
  const match = props.options.find(o => o.value === props.modelValue)
  return match ? match.label : ''
})

const activeDescendant = computed(() =>
  activeIndex.value >= 0 ? `${id}-option-${activeIndex.value}` : undefined
)

const panelStyle = computed(() => {
  void positionTick.value
  if (!isOpen.value || !selectRef.value) return { display: 'none' }
  const rect = selectRef.value.getBoundingClientRect()
  if (props.placement === 'top') {
    return { position: 'fixed', left: `${rect.left}px`, bottom: `${window.innerHeight - rect.top + 6}px`, width: `${rect.width}px` }
  }
  return { position: 'fixed', left: `${rect.left}px`, top: `${rect.bottom + 6}px`, width: `${rect.width}px` }
})

function getOptionLabel(option: SelectOption) {
  return option.label
}

function getOptionKey(option: SelectOption) {
  return String(option.value)
}

function isOptionSelected(option: SelectOption) {
  return option.value === props.modelValue
}

function toggle() {
  if (props.disabled) return
  isOpen.value ? close() : open()
}

function open() {
  isOpen.value = true
  activeIndex.value = Math.max(
    0,
    props.options.findIndex(o => o.value === props.modelValue)
  )
  if (props.searchable) {
    nextTick(() => searchRef.value?.focus())
  }
}

function close() {
  isOpen.value = false
  searchQuery.value = ''
  activeIndex.value = -1
}

function selectOption(option: SelectOption) {
  if (option.disabled) return
  emit('update:modelValue', option.value)
  emit('change', option.value)
  close()
  triggerRef.value?.focus()
}

function onTriggerKeydown(e: KeyboardEvent) {
  switch (e.key) {
    case 'Enter':
    case ' ':
      e.preventDefault()
      toggle()
      break
    case 'ArrowDown':
      e.preventDefault()
      if (!isOpen.value) open()
      else activeIndex.value = Math.min(activeIndex.value + 1, filteredOptions.value.length - 1)
      break
    case 'ArrowUp':
      e.preventDefault()
      if (!isOpen.value) open()
      else activeIndex.value = Math.max(activeIndex.value - 1, 0)
      break
    case 'Escape':
      close()
      break
  }
}

function onSearchKeydown(e: KeyboardEvent) {
  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      activeIndex.value = Math.min(activeIndex.value + 1, filteredOptions.value.length - 1)
      break
    case 'ArrowUp':
      e.preventDefault()
      activeIndex.value = Math.max(activeIndex.value - 1, 0)
      break
    case 'Enter':
      e.preventDefault()
      if (activeIndex.value >= 0 && filteredOptions.value[activeIndex.value]) {
        selectOption(filteredOptions.value[activeIndex.value])
      }
      break
    case 'Escape':
      close()
      triggerRef.value?.focus()
      break
  }
}

function handleClickOutside(e: MouseEvent) {
  const target = e.target as Node
  if (
    selectRef.value && !selectRef.value.contains(target) &&
    panelRef.value && !panelRef.value.contains(target)
  ) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside, true)
  window.addEventListener('scroll', onScroll, true)
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside, true)
  window.removeEventListener('scroll', onScroll, true)
  window.removeEventListener('resize', onResize)
})

watch(isOpen, (val) => {
  if (!val) searchQuery.value = ''
})
</script>

<style scoped>
.q-select {
  position: relative;
  width: 100%;
  font-family: var(--font-family);
}

/* ── Trigger ── */
.q-select__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0 var(--spacing-md);
  background: var(--color-surface-elevated);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  outline: none;
}

.q-select--sm .q-select__trigger {
  height: 30px;
  padding: 0 10px;
  font-size: 11px;
  gap: 4px;
}

.q-select--sm { width: auto; min-width: unset; }

.q-select--sm .q-select__chevron { width: 10px; height: 10px; }

.q-select--sm .q-select__option {
  padding: 4px 8px;
  font-size: 11px;
}
.q-select--md .q-select__trigger { height: 38px; }
.q-select--lg .q-select__trigger { height: 44px; }

.q-select__trigger:hover:not(:disabled) {
  border-color: var(--color-border-hover);
}

.q-select__trigger:focus-visible {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.q-select--open .q-select__trigger {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.q-select--disabled .q-select__trigger {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--color-surface-hover);
}

.q-select--invalid .q-select__trigger {
  border-color: var(--color-danger);
  box-shadow: 0 0 0 3px var(--color-danger-bg);
}

.q-select__value {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.q-select__placeholder {
  flex: 1;
  color: var(--color-text-muted);
}

.q-select__chevron {
  flex-shrink: 0;
  margin-left: var(--spacing-sm);
  color: var(--color-text-muted);
  transition: transform var(--transition-fast);
}

.q-select__chevron--open {
  transform: rotate(180deg);
}

/* ── Panel ── */
.q-select__panel {
  z-index: 90;
  box-sizing: border-box;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

/* Panel transition */
.q-select-panel-enter-active {
  transition: opacity 0.15s ease, transform 0.2s var(--ease-out-expo);
}
.q-select-panel-leave-active {
  transition: opacity 0.12s ease, transform 0.12s ease;
}
.q-select-panel-enter-from,
.q-select-panel-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}

/* ── Search ── */
.q-select__search-wrap {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 2px solid var(--color-border-light);
}

.q-select__search-icon {
  flex-shrink: 0;
  color: var(--color-text-muted);
}

.q-select__search {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.q-select__search::placeholder {
  color: var(--color-text-muted);
}

/* ── Options ── */
.q-select__options {
  list-style: none;
  max-height: 240px;
  overflow-y: auto;
  padding: var(--spacing-xs);
  margin: 0;
}

.q-select__option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.q-select__option:hover:not(.q-select__option--disabled),
.q-select__option--active {
  background: var(--color-surface-hover);
}

.q-select__option--selected {
  background: var(--color-primary-bg);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.q-select__option--selected:hover {
  background: var(--color-primary-bg);
}

.q-select__option--disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.q-select__option-label {
  flex: 1;
  overflow: hidden;
  word-break: break-word;
  line-height: 1.4;
}

.q-select__check {
  flex-shrink: 0;
  color: var(--color-primary);
}

.q-select__empty {
  padding: var(--spacing-lg) var(--spacing-md);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}
</style>
