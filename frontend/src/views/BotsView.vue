<template>
  <section class="view">
    <div class="container">
      <!-- Page Header — Bauhaus -->
      <div class="page-header fade-in">
        <div class="header-text">
          <p class="eyebrow">量化交易</p>
          <h1 class="page-title">{{ $t('pages.botsTitle') }}</h1>
          <p class="page-subtitle">绑定券商账户，选择策略，设置托管金额，让机器人按策略执行买卖并持续跟踪收益。</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-primary" type="button" @click="openCreateForm()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            创建托管机器人
          </button>
        </div>
      </div>

      <CreateManagedBotModal
        v-if="showCreateForm"
        :initial-strategy-id="initialStrategyId"
        @close="handleCloseCreate"
        @created="handleCreated"
      />

      <!-- Stats Bar -->
      <div v-if="!botsStore.isLoading && botsStore.items.length > 0" class="stats-bar">
        <div class="stat-chip">
          <span class="stat-chip__label">托管机器人</span>
          <span class="stat-chip__value tnum">{{ botsStore.items.length }}</span>
        </div>
        <div class="stat-chip">
          <span class="stat-chip__label">运行中</span>
          <span class="stat-chip__value tnum stat-chip__value--active">{{ botsStore.items.filter(b => b.status === 'active').length }}</span>
          <span v-if="botsStore.items.some(b => b.status === 'active')" class="stat-chip__dot"></span>
        </div>
        <div class="stat-chip">
          <span class="stat-chip__label">已暂停</span>
          <span class="stat-chip__value tnum">{{ botsStore.items.filter(b => b.status === 'paused').length }}</span>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="botsStore.isLoading" class="empty-state">
        <div class="empty-state__spinner"></div>
        加载托管机器人中...
      </div>

      <!-- Empty State -->
      <div v-else-if="botsStore.items.length === 0" class="empty-state empty-state--dashed">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        暂无托管机器人。先绑定券商账户，再用策略创建第一个量化托管机器人。
      </div>

      <!-- Bot List -->
      <div v-else class="bot-list">
        <ManagedBotCard
          v-for="(bot, index) in botsStore.items"
          :key="bot.id"
          :bot="bot"
          :style="{ animationDelay: `${index * 40}ms` }"
          @view-positions="openPositions"
          @view-detail="openDetail"
          @pause="handlePause"
          @resume="handleResume"
        />
      </div>

      <ManagedBotPositionsModal
        v-if="selectedBotId"
        :bot-id="selectedBotId"
        @close="handleCloseModal"
      />

      <ManagedBotDetailModal
        v-if="selectedDetailBot"
        :bot="selectedDetailBot"
        @close="handleCloseModal"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { LocationQueryRaw } from 'vue-router'
import CreateManagedBotModal from '../components/bots/CreateManagedBotModal.vue'
import ManagedBotCard from '../components/bots/ManagedBotCard.vue'
import ManagedBotDetailModal from '../components/bots/ManagedBotDetailModal.vue'
import ManagedBotPositionsModal from '../components/bots/ManagedBotPositionsModal.vue'
import { useBotsStore } from '../stores/bots'
import type { ManagedBot } from '../types/Bot'

const route = useRoute()
const router = useRouter()
const botsStore = useBotsStore()

const showCreateForm = ref(false)
const selectedBotId = ref<string | null>(null)
const selectedDetailBot = ref<ManagedBot | null>(null)
const initialStrategyId = ref('')

onMounted(async () => {
  await Promise.all([
    botsStore.loadBots(),
    botsStore.loadRecent(),
  ])
  syncRouteState()
})

watch(
  () => [route.query.create, route.query.strategyId, route.query.botId, route.query.modal, botsStore.items.length].join('|'),
  () => {
    syncRouteState()
  }
)

async function handleCreated() {
  showCreateForm.value = false
  await replaceQuery({
    create: undefined,
    strategyId: undefined,
  })
  await botsStore.loadRecent()
}

function openCreateForm(strategyId?: string) {
  showCreateForm.value = true
  void replaceQuery({
    create: '1',
    strategyId: strategyId || initialStrategyId.value || undefined,
    botId: undefined,
    modal: undefined,
  })
}

function handleCloseCreate() {
  showCreateForm.value = false
  void replaceQuery({
    create: undefined,
    strategyId: undefined,
  })
}

function openPositions(botId: string) {
  selectedBotId.value = botId
  selectedDetailBot.value = null
  void replaceQuery({
    create: undefined,
    strategyId: undefined,
    botId,
    modal: 'positions',
  })
}

function openDetail(botId: string) {
  selectedDetailBot.value = botsStore.items.find((bot) => bot.id === botId) ?? null
  selectedBotId.value = null
  void replaceQuery({
    create: undefined,
    strategyId: undefined,
    botId,
    modal: 'detail',
  })
}

function handleCloseModal() {
  selectedBotId.value = null
  selectedDetailBot.value = null
  void replaceQuery({
    botId: undefined,
    modal: undefined,
  })
}

async function handlePause(botId: string) {
  try {
    await botsStore.pauseBot(botId)
    await botsStore.loadRecent()
  } catch {
    // toast already handled in store
  }
}

async function handleResume(botId: string) {
  try {
    await botsStore.resumeBot(botId)
    await botsStore.loadRecent()
  } catch {
    // toast already handled in store
  }
}

function syncRouteState() {
  initialStrategyId.value = typeof route.query.strategyId === 'string' ? route.query.strategyId : ''
  showCreateForm.value = route.query.create === '1'

  const botId = typeof route.query.botId === 'string' ? route.query.botId : ''
  const modal = route.query.modal

  if (!botId) {
    selectedBotId.value = null
    selectedDetailBot.value = null
    return
  }

  if (modal === 'positions') {
    selectedBotId.value = botId
    selectedDetailBot.value = null
    return
  }

  if (modal === 'detail') {
    selectedBotId.value = null
    selectedDetailBot.value = botsStore.items.find((bot) => bot.id === botId) ?? null
    return
  }

  selectedBotId.value = null
  selectedDetailBot.value = null
}

function replaceQuery(patch: Record<string, string | undefined>) {
  const query: LocationQueryRaw = { ...route.query, ...patch }

  for (const key of Object.keys(query)) {
    const value = query[key]
    if (value === undefined || value === null || value === '') {
      delete query[key]
    }
  }

  return router.replace({ query })
}
</script>

<style scoped>
@keyframes slide-up {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.view {
  width: 100%;
}

/* ── Page Header — Bauhaus ── */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
  position: relative;
  padding-bottom: var(--spacing-lg);
}

.page-header::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 80px;
  height: 6px;
  background: var(--color-accent);
  border-radius: 3px;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.eyebrow {
  margin: 0 0 6px;
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-accent);
}

.page-title {
  margin: 0;
  font-size: var(--font-size-xxl);
  font-weight: 800;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.page-subtitle {
  margin: var(--spacing-xs) 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
  flex-shrink: 0;
}

/* ── Stats Bar ── */
.stats-bar {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.stat-chip__label {
  font-size: var(--font-size-xs);
  font-weight: 700;
  color: var(--color-text-muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.stat-chip__value {
  font-size: var(--font-size-xl);
  font-weight: 800;
  color: var(--color-text-primary);
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.stat-chip__value--active {
  color: var(--color-success);
}

.stat-chip__dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--color-success);
  animation: pulse-dot 2s ease infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ── Empty / Loading States ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xxl) var(--spacing-xl);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  text-align: center;
}

.empty-state--dashed {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
}

.empty-state__spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

/* ── Bot List ── */
.bot-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.bot-list > * {
  animation: slide-up 0.25s ease both;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .header-actions {
    width: 100%;
  }

  .header-actions .btn {
    flex: 1;
  }

  .stats-bar {
    flex-wrap: wrap;
    gap: var(--spacing-sm);
  }

  .stat-chip {
    flex: 1;
    min-width: 0;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .stats-bar {
    flex-direction: column;
  }
}
</style>
