<template>
  <div class="app">
    <TopNav />
    <main class="main-content">
      <RouterView />
    </main>
    <HelpPanel :open="userStore.helpPanelOpen" @close="userStore.setHelpPanelOpen(false)" />
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
    <footer class="app-footer">
      <div class="container footer-content">
        <span class="copyright">{{ $t('footer.copyright') }}</span>
        <div class="footer-links">
          <a href="#">{{ $t('footer.help') }}</a>
          <a href="#">{{ $t('footer.api') }}</a>
          <a href="#">{{ $t('footer.privacy') }}</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import HelpPanel from './components/help/HelpPanel.vue'
import GuidedBacktestFlow from './components/onboarding/GuidedBacktestFlow.vue'
import TopNav from './components/TopNav.vue'
import { useUserStore } from './stores'

const router = useRouter()
const userStore = useUserStore()

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
  flex-direction: column;
  background: var(--color-background);
}

.main-content {
  flex: 1;
  padding: var(--spacing-lg) 0;
}

:deep(.onboarding-highlight) {
  position: relative;
  border-radius: 16px;
  z-index: 2;
}

/* Footer */
.app-footer {
  padding: var(--spacing-lg) 0;
  border-top: 1px solid var(--color-border-light);
  margin-top: auto;
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.copyright {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.footer-links {
  display: flex;
  gap: var(--spacing-lg);
}

.footer-links a {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.footer-links a:hover {
  color: var(--color-primary);
}

@media (max-width: 768px) {
  .footer-content {
    flex-direction: column;
    gap: var(--spacing-md);
    text-align: center;
  }
}
</style>
