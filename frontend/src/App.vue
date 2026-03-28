<template>
  <div class="app" :class="{ 'no-chrome': hideChrome }">
    <TopNav v-if="!hideChrome" />
    <div class="app-body">
      <main class="main-content">
        <RouterView />
      </main>
      <StatusBar v-if="!hideChrome" />
    </div>
    <HelpPanel v-if="!hideChrome" :open="userStore.helpPanelOpen" @close="userStore.setHelpPanelOpen(false)" />
    <GuidedBacktestFlow
      v-if="userStore.guidedBacktestActive"
      :step="userStore.guidedBacktestStep || 1"
      :job-id="userStore.guidedBacktestJobId || ''"
      @exit="handleGuidedExit"
      @open-marketplace="handleOpenMarketplace"
      @open-parameters="handleOpenParameters"
      @open-report="handleOpenReport"
      @complete="handleGuidedComplete"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import HelpPanel from './components/help/HelpPanel.vue'
import GuidedBacktestFlow from './components/onboarding/GuidedBacktestFlow.vue'
import StatusBar from './components/StatusBar.vue'
import TopNav from './components/TopNav.vue'
import { useUserStore } from './stores'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const hideChrome = computed(() => route.meta.hideChrome === true)

function handleShortcut(event: KeyboardEvent) {
  const target = event.target as HTMLElement | null
  const tagName = target?.tagName?.toLowerCase()
  const typing = tagName === 'input' || tagName === 'textarea' || target?.isContentEditable

  if (!typing && (event.key === '?' || event.key === 'F1')) {
    event.preventDefault()
    userStore.setHelpPanelOpen(true)
  }

  if (event.key === 'Escape' && userStore.helpPanelOpen) {
    userStore.setHelpPanelOpen(false)
  }
}

function handleGuidedExit() {
  userStore.cancelGuidedBacktest()
}

function handleOpenMarketplace(strategyId: string) {
  userStore.setGuidedBacktestStrategy(strategyId)
  userStore.setGuidedBacktestStep(1)
  userStore.setOnboardingHighlightTarget('guided-strategy-card')
  void router.push({ name: 'strategy-library', query: { guided: 'true', onboardingStrategyId: strategyId } })
}

function handleOpenParameters(strategyId: string) {
  userStore.setGuidedBacktestStrategy(strategyId)
  userStore.setGuidedBacktestStep(2)
  userStore.setOnboardingHighlightTarget('guided-run-button')
  void router.push({ name: 'strategy-parameters', params: { strategyId }, query: { guided: 'true' } })
}

function handleOpenReport(jobId: string) {
  userStore.setGuidedBacktestJob(jobId)
  userStore.setGuidedBacktestStep(4)
  userStore.setOnboardingHighlightTarget('backtest-results-section')
  void router.push({ name: 'backtest-report', params: { jobId }, query: { guided: 'true' } })
}

async function handleGuidedComplete() {
  await userStore.markOnboardingCompleted(true)
  userStore.finishGuidedBacktest()
}

onMounted(() => {
  void userStore.loadProfile()
  window.addEventListener('keydown', handleShortcut)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleShortcut)
})
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  background: var(--color-background);
}

/* Sidebar layout: sidebar on left, content takes remaining space */
.app-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: var(--sidebar-width);
  min-height: 100vh;
}

.app.no-chrome .app-body {
  margin-left: 0;
}

.main-content {
  flex: 1;
  padding: var(--spacing-md);
  overflow-y: auto;
}

:deep(.onboarding-highlight) {
  position: relative;
  border-radius: var(--radius-lg);
  z-index: 2;
}

/* Mobile: bottom nav instead of sidebar */
@media (max-width: 768px) {
  .app-body {
    margin-left: 0;
    padding-bottom: var(--sidebar-width);
  }

  .main-content {
    padding: var(--spacing-sm);
  }
}
</style>
