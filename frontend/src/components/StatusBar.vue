<template>
  <div class="status-bar">
    <div class="status-left">
      <div class="status-item">
        <span class="status-dot" :class="connectionStatus" />
        <span>{{ connectionLabel }}</span>
      </div>
      <div class="status-divider" />
      <div class="status-item">
        <span class="status-label">DATA</span>
        <span>{{ dataSource }}</span>
      </div>
      <div class="status-divider" />
      <div class="status-item">
        <span class="status-label">MKT</span>
        <span>{{ marketStyle }}</span>
      </div>
    </div>
    <div class="status-right">
      <div class="status-item">
        <span class="status-label">UPD</span>
        <span class="tnum">{{ lastUpdate }}</span>
      </div>
      <div class="status-divider" />
      <div class="status-item tnum">{{ currentTime }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

const currentTime = ref(formatTime())
let timer: ReturnType<typeof setInterval> | null = null

function formatTime() {
  const now = new Date()
  return now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const connectionStatus = computed(() => 'online')
const connectionLabel = computed(() => 'CONNECTED')
const dataSource = computed(() => 'JQData')
const marketStyle = computed(() => {
  const style = (userStore.profile as any)?.marketStyle ?? (userStore.profile as any)?.market_style
  return style === 'us' ? 'US' : 'CN'
})

const lastUpdate = computed(() => {
  return formatTime()
})

onMounted(() => {
  timer = setInterval(() => {
    currentTime.value = formatTime()
  }, 1000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.status-bar {
  height: var(--status-bar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-md);
  background: var(--color-nav-bg);
  border-top: 1px solid var(--color-border);
  font-family: var(--font-mono);
  font-size: var(--font-size-2xs);
  color: var(--color-text-muted);
  flex-shrink: 0;
  user-select: none;
}

.status-left,
.status-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.status-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-label {
  color: var(--color-text-muted);
  font-weight: var(--font-weight-medium);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.status-dot.online {
  background: var(--color-success);
  box-shadow: 0 0 4px var(--color-success);
}

.status-dot.offline {
  background: var(--color-danger);
}

.status-dot.connecting {
  background: var(--color-warning);
}

.status-divider {
  width: 1px;
  height: 12px;
  background: var(--color-border);
}
</style>
