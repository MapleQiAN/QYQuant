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

      <div v-if="simulationStore.bots.length" class="bot-list">
        <article
          v-for="bot in simulationStore.bots"
          :key="bot.id"
          class="bot-card"
        >
          <p class="bot-name">Strategy ID: {{ bot.strategy_id }}</p>
          <p class="bot-meta">Initial Capital: {{ bot.initial_capital }}</p>
          <p class="bot-meta">Status: {{ bot.status }}</p>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import CreateBotModal from '../components/simulation/CreateBotModal.vue'
import SimulationDisclaimerModal from '../components/simulation/SimulationDisclaimerModal.vue'
import { useSimulationStore } from '../stores/useSimulationStore'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const simulationStore = useSimulationStore()

const showCreateForm = ref(false)

const showDisclaimer = computed(() => (
  Boolean(userStore.profile.id) && !userStore.profile.sim_disclaimer_accepted
))

onMounted(async () => {
  await userStore.loadProfile()
})

async function handleDisclaimerAccepted() {
  await userStore.refreshProfile()
}

function handleCreated() {
  showCreateForm.value = false
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

.bot-list {
  display: grid;
  gap: 12px;
}

.bot-card {
  padding: 18px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.85);
}

.bot-name {
  margin: 0 0 8px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.bot-meta {
  margin: 0;
  color: var(--color-text-secondary);
}
</style>
