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
          @click="showCreateForm = true"
        >
          Create Bot
        </button>
      </div>

      <CreateBotModal
        v-if="showCreateForm"
        @close="showCreateForm = false"
        @created="handleCreated"
      />

      <div v-if="simulationStore.isLoading" class="loading-hint">加载中...</div>

      <div v-else-if="simulationStore.bots.length === 0" class="empty-hint">
        还没有机器人，点击 "Create Bot" 开始
      </div>

      <div v-else class="bot-list">
        <BotCard
          v-for="bot in simulationStore.bots"
          :key="bot.id"
          :bot="bot"
          @view-positions="openPositions"
        />
      </div>

      <BotPositionsModal
        v-if="selectedBotId"
        :bot-id="selectedBotId"
        @close="selectedBotId = null"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import BotCard from '../components/simulation/BotCard.vue'
import BotPositionsModal from '../components/simulation/BotPositionsModal.vue'
import CreateBotModal from '../components/simulation/CreateBotModal.vue'
import SimulationDisclaimerModal from '../components/simulation/SimulationDisclaimerModal.vue'
import { useSimulationStore } from '../stores/useSimulationStore'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const simulationStore = useSimulationStore()

const showCreateForm = ref(false)
const selectedBotId = ref<string | null>(null)

const showDisclaimer = computed(() => (
  Boolean(userStore.profile.id) && !userStore.profile.sim_disclaimer_accepted
))

onMounted(async () => {
  await userStore.loadProfile()
  await simulationStore.fetchBots()
})

async function handleDisclaimerAccepted() {
  await userStore.refreshProfile()
}

async function handleCreated() {
  showCreateForm.value = false
  await simulationStore.fetchBots()
}

function openPositions(botId: string) {
  selectedBotId.value = botId
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
  background: #111827;
  color: #fff;
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
