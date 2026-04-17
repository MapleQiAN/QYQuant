<template>
  <section class="view">
    <div class="container">
      <div class="hero">
        <div>
          <h1 class="view-title">{{ $t('pages.botsTitle') }}</h1>
          <p class="view-subtitle">绑定券商账户，选择策略，设置托管金额，让机器人按策略执行买卖并持续跟踪收益。</p>
        </div>
        <button class="create-button" type="button" @click="openCreateForm()">创建托管机器人</button>
      </div>

      <CreateManagedBotModal
        v-if="showCreateForm"
        :initial-strategy-id="initialStrategyId"
        @close="handleCloseCreate"
        @created="handleCreated"
      />

      <div v-if="botsStore.isLoading" class="loading-hint">加载托管机器人中...</div>
      <div v-else-if="botsStore.items.length === 0" class="empty-hint">
        暂无托管机器人。先绑定券商账户，再用策略创建第一个量化托管机器人。
      </div>
      <div v-else class="bot-list">
        <ManagedBotCard
          v-for="bot in botsStore.items"
          :key="bot.id"
          :bot="bot"
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
.view {
  width: 100%;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 24px;
}

.view-title {
  margin: 0 0 var(--spacing-sm);
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.view-subtitle {
  margin: 0;
  color: var(--color-text-muted);
  max-width: 720px;
}

.create-button {
  min-height: 46px;
  padding: 0 18px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
  color: var(--color-text-inverse);
  cursor: pointer;
  white-space: nowrap;
}

.loading-hint,
.empty-hint {
  padding: 28px;
  text-align: center;
  color: var(--color-text-muted);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.7);
}

.bot-list {
  display: grid;
  gap: 14px;
}

@media (max-width: 768px) {
  .hero {
    flex-direction: column;
  }

  .create-button {
    width: 100%;
  }
}
</style>
