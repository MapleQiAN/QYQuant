<template>
  <div
    ref="pickerRef"
    class="q-datepicker"
    :class="[
      `q-datepicker--${size}`,
      { 'q-datepicker--open': isOpen, 'q-datepicker--disabled': disabled, 'q-datepicker--invalid': invalid }
    ]"
  >
    <button
      ref="triggerRef"
      type="button"
      class="q-datepicker__trigger"
      :disabled="disabled"
      :aria-expanded="isOpen"
      @click="toggle"
      @keydown="onTriggerKeydown"
    >
      <svg class="q-datepicker__icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
        <line x1="16" y1="2" x2="16" y2="6" />
        <line x1="8" y1="2" x2="8" y2="6" />
        <line x1="3" y1="10" x2="21" y2="10" />
      </svg>

      <span v-if="formattedDate" class="q-datepicker__value">{{ formattedDate }}</span>
      <span v-else class="q-datepicker__placeholder">{{ placeholder }}</span>

      <svg class="q-datepicker__chevron" :class="{ 'q-datepicker__chevron--open': isOpen }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="6 9 12 15 18 9" />
      </svg>
    </button>

    <Transition name="q-datepicker-panel">
      <div v-if="isOpen" class="q-datepicker__panel" :style="panelStyle">
        <!-- Header -->
        <div class="q-datepicker__header">
          <button type="button" class="q-datepicker__nav-btn" @click="prevYear" :aria-label="'Previous year'">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="11 17 6 12 11 7" /><polyline points="18 17 13 12 18 7" /></svg>
          </button>
          <button type="button" class="q-datepicker__nav-btn" @click="prevMonth" :aria-label="'Previous month'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6" /></svg>
          </button>

          <button type="button" class="q-datepicker__title" @click="goToToday">
            {{ headerLabel }}
          </button>

          <button type="button" class="q-datepicker__nav-btn" @click="nextMonth" :aria-label="'Next month'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6" /></svg>
          </button>
          <button type="button" class="q-datepicker__nav-btn" @click="nextYear" :aria-label="'Next year'">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="13 17 18 12 13 7" /><polyline points="6 17 11 12 6 7" /></svg>
          </button>
        </div>

        <!-- Weekday headers -->
        <div class="q-datepicker__weekdays">
          <span v-for="day in weekdayLabels" :key="day" class="q-datepicker__weekday">{{ day }}</span>
        </div>

        <!-- Calendar grid -->
        <div class="q-datepicker__grid">
          <button
            v-for="(cell, index) in calendarCells"
            :key="index"
            type="button"
            class="q-datepicker__cell"
            :class="{
              'q-datepicker__cell--other': !cell.currentMonth,
              'q-datepicker__cell--today': cell.isToday,
              'q-datepicker__cell--selected': cell.isSelected,
              'q-datepicker__cell--in-range': cell.inRange,
              'q-datepicker__cell--range-start': cell.isRangeStart,
              'q-datepicker__cell--range-end': cell.isRangeEnd,
              'q-datepicker__cell--disabled': cell.disabled
            }"
            :disabled="cell.disabled"
            @click="selectDay(cell)"
            @mouseenter="onCellHover(cell)"
          >
            {{ cell.day }}
          </button>
        </div>

        <!-- Footer -->
        <div class="q-datepicker__footer">
          <button type="button" class="q-datepicker__footer-btn" @click="goToToday">
            {{ todayLabel }}
          </button>
          <button v-if="clearable && modelValue" type="button" class="q-datepicker__footer-btn q-datepicker__footer-btn--danger" @click="clearValue">
            {{ clearLabel }}
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

const props = withDefaults(defineProps<{
  modelValue: string | null
  placeholder?: string
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
  invalid?: boolean
  clearable?: boolean
  placement?: 'bottom' | 'top'
  minDate?: string | null
  maxDate?: string | null
  locale?: string
}>(), {
  placeholder: 'Select date...',
  disabled: false,
  size: 'md',
  invalid: false,
  clearable: true,
  placement: 'bottom',
  minDate: null,
  maxDate: null,
  locale: 'en',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | null): void
  (e: 'change', value: string | null): void
}>()

const pickerRef = ref<HTMLElement | null>(null)
const triggerRef = ref<HTMLButtonElement | null>(null)
const isOpen = ref(false)
const viewYear = ref(new Date().getFullYear())
const viewMonth = ref(new Date().getMonth())

// Locale-aware labels
const months = computed(() =>
  props.locale === 'zh'
    ? ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
    : ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
)

const weekdays = computed(() =>
  props.locale === 'zh'
    ? ['一', '二', '三', '四', '五', '六', '日']
    : ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
)

const todayLabel = computed(() => props.locale === 'zh' ? '今天' : 'Today')
const clearLabel = computed(() => props.locale === 'zh' ? '清除' : 'Clear')

const weekdayLabels = computed(() => weekdays.value)

const headerLabel = computed(() =>
  props.locale === 'zh'
    ? `${viewYear.value}年 ${months.value[viewMonth.value]}`
    : `${months.value[viewMonth.value]} ${viewYear.value}`
)

const formattedDate = computed(() => {
  if (!props.modelValue) return ''
  const d = new Date(props.modelValue + 'T00:00:00')
  if (isNaN(d.getTime())) return props.modelValue
  if (props.locale === 'zh') {
    return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
  }
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
})

const panelStyle = computed(() =>
  props.placement === 'top' ? { bottom: 'calc(100% + 6px)' } : { top: 'calc(100% + 6px)' }
)

interface CalendarCell {
  day: number
  date: string
  currentMonth: boolean
  isToday: boolean
  isSelected: boolean
  inRange: boolean
  isRangeStart: boolean
  isRangeEnd: boolean
  disabled: boolean
}

const calendarCells = computed<CalendarCell[]>(() => {
  const year = viewYear.value
  const month = viewMonth.value
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)

  // Monday = 0, Sunday = 6
  let startDow = firstDay.getDay() - 1
  if (startDow < 0) startDow = 6

  const cells: CalendarCell[] = []
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const selectedDate = props.modelValue ? new Date(props.modelValue + 'T00:00:00') : null

  // Previous month padding
  const prevMonthLast = new Date(year, month, 0).getDate()
  for (let i = startDow - 1; i >= 0; i--) {
    const day = prevMonthLast - i
    const d = new Date(year, month - 1, day)
    cells.push(makeCell(day, d, false, today, selectedDate))
  }

  // Current month
  for (let day = 1; day <= lastDay.getDate(); day++) {
    const d = new Date(year, month, day)
    cells.push(makeCell(day, d, true, today, selectedDate))
  }

  // Next month padding
  const remaining = 42 - cells.length
  for (let day = 1; day <= remaining; day++) {
    const d = new Date(year, month + 1, day)
    cells.push(makeCell(day, d, false, today, selectedDate))
  }

  return cells
})

function makeCell(day: number, d: Date, currentMonth: boolean, today: Date, selectedDate: Date | null): CalendarCell {
  const dateStr = formatDate(d)
  return {
    day,
    date: dateStr,
    currentMonth,
    isToday: d.getTime() === today.getTime(),
    isSelected: selectedDate !== null && d.getTime() === selectedDate.getTime(),
    inRange: false,
    isRangeStart: false,
    isRangeEnd: false,
    disabled: isDateDisabled(d),
  }
}

function formatDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function isDateDisabled(d: Date): boolean {
  if (props.minDate) {
    const min = new Date(props.minDate + 'T00:00:00')
    if (d < min) return true
  }
  if (props.maxDate) {
    const max = new Date(props.maxDate + 'T00:00:00')
    if (d > max) return true
  }
  return false
}

function toggle() {
  if (props.disabled) return
  isOpen.value ? close() : open()
}

function open() {
  isOpen.value = true
  if (props.modelValue) {
    const d = new Date(props.modelValue + 'T00:00:00')
    if (!isNaN(d.getTime())) {
      viewYear.value = d.getFullYear()
      viewMonth.value = d.getMonth()
    }
  }
}

function close() {
  isOpen.value = false
}

function selectDay(cell: CalendarCell) {
  if (cell.disabled || !cell.currentMonth) return
  emit('update:modelValue', cell.date)
  emit('change', cell.date)
  close()
  triggerRef.value?.focus()
}

function onCellHover(_cell: CalendarCell) {
  // future: range selection hover preview
}

function goToToday() {
  const now = new Date()
  viewYear.value = now.getFullYear()
  viewMonth.value = now.getMonth()
}

function prevMonth() {
  if (viewMonth.value === 0) {
    viewMonth.value = 11
    viewYear.value--
  } else {
    viewMonth.value--
  }
}

function nextMonth() {
  if (viewMonth.value === 11) {
    viewMonth.value = 0
    viewYear.value++
  } else {
    viewMonth.value++
  }
}

function prevYear() {
  viewYear.value--
}

function nextYear() {
  viewYear.value++
}

function clearValue() {
  emit('update:modelValue', null)
  emit('change', null)
}

function onTriggerKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    toggle()
  } else if (e.key === 'Escape') {
    close()
  }
}

function handleClickOutside(e: MouseEvent) {
  if (pickerRef.value && !pickerRef.value.contains(e.target as Node)) {
    close()
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside, true))
onUnmounted(() => document.removeEventListener('click', handleClickOutside, true))
</script>

<style scoped>
.q-datepicker {
  position: relative;
  width: 100%;
  font-family: var(--font-family);
}

/* ── Trigger ── */
.q-datepicker__trigger {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
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

.q-datepicker--sm .q-datepicker__trigger { height: 32px; }
.q-datepicker--md .q-datepicker__trigger { height: 38px; }
.q-datepicker--lg .q-datepicker__trigger { height: 44px; }

.q-datepicker__trigger:hover:not(:disabled) {
  border-color: var(--color-border-hover);
}

.q-datepicker__trigger:focus-visible {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.q-datepicker--open .q-datepicker__trigger {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.q-datepicker--disabled .q-datepicker__trigger {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--color-surface-hover);
}

.q-datepicker--invalid .q-datepicker__trigger {
  border-color: var(--color-danger);
  box-shadow: 0 0 0 3px var(--color-danger-bg);
}

.q-datepicker__icon {
  flex-shrink: 0;
  color: var(--color-text-muted);
}

.q-datepicker__value {
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.q-datepicker__placeholder {
  flex: 1;
  text-align: left;
  color: var(--color-text-muted);
}

.q-datepicker__chevron {
  flex-shrink: 0;
  color: var(--color-text-muted);
  transition: transform var(--transition-fast);
}

.q-datepicker__chevron--open {
  transform: rotate(180deg);
}

/* ── Panel ── */
.q-datepicker__panel {
  position: absolute;
  left: 0;
  z-index: 50;
  width: 290px;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.q-datepicker-panel-enter-active {
  transition: opacity 0.15s ease, transform 0.2s var(--ease-out-expo);
}
.q-datepicker-panel-leave-active {
  transition: opacity 0.12s ease, transform 0.12s ease;
}
.q-datepicker-panel-enter-from,
.q-datepicker-panel-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}

/* ── Header ── */
.q-datepicker__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) var(--spacing-sm);
  border-bottom: 2px solid var(--color-border-light);
  background: var(--color-surface-elevated);
}

.q-datepicker__nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.q-datepicker__nav-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
  border-color: var(--color-border-hover);
}

.q-datepicker__title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  background: none;
  border: 2px solid transparent;
  border-radius: var(--radius-sm);
  padding: var(--spacing-xs) var(--spacing-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  font-family: var(--font-family);
}

.q-datepicker__title:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-border);
}

/* ── Weekdays ── */
.q-datepicker__weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  padding: var(--spacing-xs) var(--spacing-sm);
  gap: 2px;
}

.q-datepicker__weekday {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wider);
}

/* ── Grid ── */
.q-datepicker__grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  padding: 0 var(--spacing-sm) var(--spacing-sm);
  gap: 2px;
}

.q-datepicker__cell {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 34px;
  border-radius: var(--radius-sm);
  border: 2px solid transparent;
  background: transparent;
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.q-datepicker__cell:hover:not(.q-datepicker__cell--disabled):not(.q-datepicker__cell--selected) {
  background: var(--color-surface-hover);
  border-color: var(--color-border);
}

.q-datepicker__cell--other {
  color: var(--color-text-muted);
  opacity: 0.5;
}

.q-datepicker__cell--today {
  border-color: var(--color-border);
  font-weight: var(--font-weight-bold);
}

.q-datepicker__cell--selected {
  background: var(--color-primary);
  color: #ffffff;
  border-color: var(--color-primary-dark);
  font-weight: var(--font-weight-bold);
}

.q-datepicker__cell--selected:hover {
  background: var(--color-primary-dark);
}

.q-datepicker__cell--disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* ── Footer ── */
.q-datepicker__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-top: 2px solid var(--color-border-light);
}

.q-datepicker__footer-btn {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-family: var(--font-family);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
  background: none;
  border: 2px solid transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.q-datepicker__footer-btn:hover {
  background: var(--color-primary-bg);
  border-color: var(--color-primary-border);
}

.q-datepicker__footer-btn--danger {
  color: var(--color-danger);
}

.q-datepicker__footer-btn--danger:hover {
  background: var(--color-danger-bg);
  border-color: var(--color-danger);
}
</style>
