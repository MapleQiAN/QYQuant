<template>
  <section class="view">
    <div class="container">
      <h1 class="view-title">{{ $t('pages.botsTitle') }}</h1>
      <p class="view-subtitle">{{ $t('pages.botsSubtitle') }}</p>

      <SimulationDisclaimerModal
        v-if="showDisclaimer"
        @accepted="handleDisclaimerAccepted"
      />

      <div class="toolbar">
        <button
          class="create-button"
          type="button"
          @click="openCreateForm()"
        >
          Create Simulation Bot
        </button>
      </div>

      <CreateBotModal
        v-if="showCreateForm"
        :initial-strategy-id="initialStrategyId"
        @close="handleCloseCreate"
        @created="handleCreated"
      />

      <div v-if="simulationStore.isLoading" class="loading-hint">Loading bots...</div>

      <div v-else-if="simulationStore.bots.length === 0" class="empty-hint">
        No simulation bots yet. Use "Create Simulation Bot" to start paper trading.
      </div>

      <div v-else class="bot-list">
        <BotCard
          v-for="bot in simulationStore.bots"
          :key="bot.id"
          :bot="bot"
          @view-positions="openPositions"
          @view-detail="openDetail"
          @pause="handlePause"
          @resume="handleResume"
          @delete="handleDelete"
        />
      </div>

      <BotPositionsModal
        v-if="selectedBotId"
        :bot-id="selectedBotId"
        @close="handleCloseModal"
      />

      <BotDetailModal
        v-if="selectedDetailBot"
        :bot="selectedDetailBot"
        @close="handleCloseModal"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { LocationQueryRaw } from 'vue-router'
import BotCard from '../components/simulation/BotCard.vue'
import BotDetailModal from '../components/simulation/BotDetailModal.vue'
import BotPositionsModal from '../components/simulation/BotPositionsModal.vue'
import CreateBotModal from '../components/simulation/CreateBotModal.vue'
import SimulationDisclaimerModal from '../components/simulation/SimulationDisclaimerModal.vue'
import { useSimulationStore } from '../stores/useSimulationStore'
import { useUserStore } from '../stores/user'
import type { SimulationBot } from '../types/Simulation'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const simulationStore = useSimulationStore()

const showCreateForm = ref(false)
const selectedBotId = ref<string | null>(null)
const selectedDetailBot = ref<SimulationBot | null>(null)
const initialStrategyId = ref('')

const showDisclaimer = computed(() => (
  Boolean(userStore.profile.id) && !userStore.profile.sim_disclaimer_accepted
))

onMounted(async () => {
  await userStore.loadProfile()
  await simulationStore.fetchBots()
  syncRouteState()
})

watch(
  () => [route.query.create, route.query.strategyId, route.query.botId, route.query.modal].join('|'),
  () => {
    syncRouteState()
  }
)

async function handleDisclaimerAccepted() {
  await userStore.refreshProfile()
}

async function handleCreated() {
  showCreateForm.value = false
  await replaceQuery({
    create: undefined,
    strategyId: undefined
  })
  await simulationStore.fetchBots()
}

function openCreateForm(strategyId?: string) {
  showCreateForm.value = true
  void replaceQuery({
    create: '1',
    strategyId: strategyId || initialStrategyId.value || undefined,
    botId: undefined,
    modal: undefined
  })
}

function handleCloseCreate() {
  showCreateForm.value = false
  void replaceQuery({
    create: undefined,
    strategyId: undefined
  })
}

function openPositions(botId: string) {
  selectedBotId.value = botId
  selectedDetailBot.value = null
  void replaceQuery({
    create: undefined,
    strategyId: undefined,
    botId,
    modal: 'positions'
  })
}

function openDetail(botId: string) {
  selectedDetailBot.value = simulationStore.bots.find((bot) => bot.id === botId) ?? null
  selectedBotId.value = null
  void replaceQuery({
    create: undefined,
    strategyId: undefined,
    botId,
    modal: 'detail'
  })
}

function handleCloseModal() {
  selectedBotId.value = null
  selectedDetailBot.value = null
  void replaceQuery({
    botId: undefined,
    modal: undefined
  })
}

async function handlePause(botId: string) {
  try {
    await simulationStore.pauseBot(botId)
  } catch {
    // Reserved for toast integration.
  }
}

async function handleResume(botId: string) {
  try {
    await simulationStore.resumeBot(botId)
  } catch {
    // Reserved for toast integration.
  }
}

async function handleDelete(botId: string) {
  if (!confirm('Delete this bot? Historical data will be preserved, but the slot will be released.')) return

  try {
    await simulationStore.deleteBot(botId)
    if (selectedBotId.value === botId || selectedDetailBot.value?.id === botId) {
      handleCloseModal()
    }
  } catch {
    // Reserved for toast integration.
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
    selectedDetailBot.value = simulationStore.bots.find((bot) => bot.id === botId) ?? null
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

.view-title {
  margin: 0 0 var(--spacing-sm);
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.view-subtitle {
  margin: 0 0 24px;
  color: var(--color-text-muted);
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

.create-button {
  min-height: 44px;
  padding: 0 18px;
  border: none;
  border-radius: 999px;
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  cursor: pointer;
}

.loading-hint,
.empty-hint {
  padding: 24px;
  text-align: center;
  color: var(--color-text-muted);
}

.bot-list {
  display: grid;
  gap: 12px;
}
</style>
