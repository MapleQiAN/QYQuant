<template>
  <div class="app" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <SideNav
      v-if="!hideChrome"
      :collapsed="sidebarCollapsed"
      @toggle="sidebarCollapsed = !sidebarCollapsed"
    />
    <div
      v-if="!hideChrome && !sidebarCollapsed"
      class="mobile-overlay"
      @click="sidebarCollapsed = true"
    />
    <div class="app-main" :class="{ 'no-sidebar': hideChrome }">
      <TopNav v-if="!hideChrome" @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed" />
      <main class="main-content">
        <RouterView />
      </main>
      <footer v-if="!hideChrome" class="app-footer">
        <div class="footer-content">
          <span class="copyright">{{ $t('footer.copyright') }}</span>
          <div class="footer-links">
            <a href="#">{{ $t('footer.help') }}</a>
            <a href="#">{{ $t('footer.api') }}</a>
            <a href="#">{{ $t('footer.privacy') }}</a>
          </div>
        </div>
      </footer>
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
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import HelpPanel from './components/help/HelpPanel.vue'
import GuidedBacktestFlow from './components/onboarding/GuidedBacktestFlow.vue'
import SideNav from './components/SideNav.vue'
import TopNav from './components/TopNav.vue'
import { useUserStore } from './stores'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const hideChrome = computed(() => route.meta.hideChrome === true)
const sidebarCollapsed = ref(window.innerWidth <= 1024)

function handleResize() {
  if (window.innerWidth <= 768) {
    sidebarCollapsed.value = true
  }
}

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
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleShortcut)
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  background: var(--color-background);
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  margin-left: var(--sidebar-width);
  transition: margin-left 250ms var(--ease-out-expo);
}

.sidebar-collapsed .app-main {
  margin-left: var(--sidebar-collapsed-width);
}

.app-main.no-sidebar {
  margin-left: 0;
}

.main-content {
  flex: 1;
  padding: var(--spacing-lg);
}

:deep(.onboarding-highlight) {
  position: relative;
  border-radius: 16px;
  z-index: 2;
}

/* Footer */
.app-footer {
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border);
  margin-top: auto;
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.copyright {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.footer-links {
  display: flex;
  gap: var(--spacing-lg);
}

.footer-links a {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.footer-links a:hover {
  color: var(--color-text-secondary);
}

/* Large screen */
@media (min-width: 1920px) {
  .main-content {
    padding: var(--spacing-xl);
  }
}

@media (min-width: 2560px) {
  .main-content {
    padding: var(--spacing-xxl) var(--spacing-xl);
  }
}

/* Mobile overlay */
.mobile-overlay {
  display: none;
}

/* Responsive */
@media (max-width: 1024px) {
  .main-content {
    padding: var(--spacing-md);
  }
}

@media (max-width: 768px) {
  .app-main {
    margin-left: 0;
  }

  .sidebar-collapsed .app-main {
    margin-left: 0;
  }

  .main-content {
    padding: var(--spacing-sm);
  }

  .footer-content {
    flex-direction: column;
    gap: var(--spacing-sm);
    text-align: center;
  }

  .mobile-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: var(--color-overlay);
    z-index: 105;
  }

  .app-footer {
    padding: var(--spacing-sm) var(--spacing-md);
  }
}

@media (max-width: 480px) {
  .main-content {
    padding: var(--spacing-xs);
  }

  .app-footer {
    padding: var(--spacing-xs) var(--spacing-sm);
  }

  .footer-links {
    gap: var(--spacing-md);
  }
}
</style>
