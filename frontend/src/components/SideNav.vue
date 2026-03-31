<template>
  <aside :class="['side-nav', { collapsed }]">
    <div class="sidebar-header">
      <div class="logo-area">
        <div class="logo-icon">
          <img :src="logoUrl" alt="QY Quant" class="logo-image" />
        </div>
        <Transition name="fade">
          <span v-if="!collapsed" class="logo-text">QY Quant</span>
        </Transition>
      </div>
    </div>

    <div class="sidebar-nav">
      <div class="nav-section">
        <span v-if="!collapsed" class="nav-section-label">{{ $t('nav.overview') || 'OVERVIEW' }}</span>
        <RouterLink
          v-for="item in mainItems"
          :key="item.id"
          :to="item.to"
          :class="['nav-item', { active: isActive(item) }]"
          :data-onboarding-target="item.target"
        >
          <span class="nav-item-indicator" />
          <component :is="item.iconComponent" class="nav-item-icon" />
          <Transition name="fade">
            <span v-if="!collapsed" class="nav-item-label">{{ t(item.label) }}</span>
          </Transition>
        </RouterLink>
      </div>

      <div class="nav-section">
        <span v-if="!collapsed" class="nav-section-label">{{ $t('nav.community') || 'COMMUNITY' }}</span>
        <RouterLink
          v-for="item in communityItems"
          :key="item.id"
          :to="item.to"
          :class="['nav-item', { active: isActive(item) }]"
        >
          <span class="nav-item-indicator" />
          <component :is="item.iconComponent" class="nav-item-icon" />
          <Transition name="fade">
            <span v-if="!collapsed" class="nav-item-label">{{ $t(item.label) }}</span>
          </Transition>
        </RouterLink>
      </div>

      <div class="nav-section">
        <span v-if="!collapsed" class="nav-section-label">{{ $t('nav.learnSection') || 'LEARN' }}</span>
        <RouterLink
          v-for="item in learnItems"
          :key="item.id"
          :to="item.to"
          :class="['nav-item', { active: isActive(item) }]"
        >
          <span class="nav-item-indicator" />
          <component :is="item.iconComponent" class="nav-item-icon" />
          <Transition name="fade">
            <span v-if="!collapsed" class="nav-item-label">{{ t(item.label) }}</span>
          </Transition>
        </RouterLink>
      </div>
    </div>

    <button class="collapse-btn footer-collapse-btn" type="button" :aria-label="collapsed ? t('common.expandSidebar') : t('common.collapseSidebar')" @click="$emit('toggle')">
      <ChevronIcon :class="{ 'rotate-180': collapsed }" />
    </button>

    <div class="sidebar-footer">
      <RouterLink
        to="/settings"
        :class="['nav-item', { active: route.path === '/settings' }]"
      >
        <span class="nav-item-indicator" />
        <SettingsIcon class="nav-item-icon" />
        <Transition name="fade">
          <span v-if="!collapsed" class="nav-item-label">{{ $t('common.settings') }}</span>
        </Transition>
      </RouterLink>
      <div v-if="!collapsed" class="plan-badge" :class="planBadgeClass" @click="handlePlanBadgeClick">
        {{ currentLevel }}
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { h, computed } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { storeToRefs } from 'pinia'
import { useUserStore } from '../stores/user'
import logoUrl from '../logo.png'

defineProps<{ collapsed: boolean }>()
defineEmits<{ toggle: [] }>()

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const userStore = useUserStore()
const { profile } = storeToRefs(userStore)

const currentLevel = computed(() => {
  if (!userStore.token) return 'FREE'
  return (profile.value.level || 'FREE').toUpperCase()
})

const planBadgeClass = computed(() => ({
  'plan-badge--free': currentLevel.value === 'FREE',
  'plan-badge--plus': currentLevel.value === 'PLUS',
  'plan-badge--pro': currentLevel.value === 'PRO',
  'plan-badge--ultra': currentLevel.value === 'ULTRA',
}))

interface NavItem {
  id: string
  to: string
  label: string
  iconComponent: any
  target?: string | null
  matchPrefix?: string
}

const mainItems: NavItem[] = [
  { id: 'dashboard', to: '/', label: 'nav.dashboard', iconComponent: DashboardIcon, target: null },
  { id: 'strategies', to: '/strategies', label: 'common.newStrategy', iconComponent: StrategyIcon, target: 'strategy-library-entry', matchPrefix: '/strategies' },
  { id: 'backtests', to: '/backtests', label: 'nav.backtests', iconComponent: BacktestIcon, target: null, matchPrefix: '/backtests' },
  { id: 'bots', to: '/bots', label: 'nav.bots', iconComponent: BotIcon, target: null, matchPrefix: '/bots' },
]

const communityItems: NavItem[] = [
  { id: 'forum', to: '/forum', label: 'nav.forum', iconComponent: ForumIcon, matchPrefix: '/forum' },
  { id: 'marketplace', to: '/marketplace', label: 'nav.marketplace', iconComponent: MarketplaceIcon, matchPrefix: '/marketplace' },
]

const learnItems: NavItem[] = [
  { id: 'learn', to: '/learn', label: 'nav.learn', iconComponent: LearnIcon, target: null, matchPrefix: '/learn' },
]

function isActive(item: NavItem) {
  if (item.to === '/') return route.path === '/'
  if (item.matchPrefix) return route.path.startsWith(item.matchPrefix)
  return route.path === item.to
}

function handlePlanBadgeClick() {
  if (!userStore.token) {
    router.push('/login')
    return
  }
  router.push('/pricing')
}

// ── Icons ──

function DashboardIcon() {
  return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.75, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('rect', { x: 3, y: 3, width: 7, height: 9, rx: 1 }),
    h('rect', { x: 14, y: 3, width: 7, height: 5, rx: 1 }),
    h('rect', { x: 14, y: 12, width: 7, height: 9, rx: 1 }),
    h('rect', { x: 3, y: 16, width: 7, height: 5, rx: 1 }),
  ])
}

function StrategyIcon() {
  return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.75, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('circle', { cx: 12, cy: 12, r: 10 }),
    h('circle', { cx: 12, cy: 12, r: 6 }),
    h('circle', { cx: 12, cy: 12, r: 2 }),
  ])
}

function BacktestIcon() {
  return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.75, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('path', { d: 'M3 3v18h18' }),
    h('path', { d: 'M7 16l4-8 4 5 5-9' }),
  ])
}

function BotIcon() {
  return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.75, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('rect', { x: 3, y: 11, width: 18, height: 10, rx: 2 }),
    h('circle', { cx: 12, cy: 5, r: 2 }),
    h('path', { d: 'M12 7v4' }),
    h('circle', { cx: 8, cy: 16, r: 1 }),
    h('circle', { cx: 16, cy: 16, r: 1 }),
  ])
}

function LearnIcon() {
  return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.75, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('path', { d: 'M4 19.5A2.5 2.5 0 0 1 6.5 17H20' }),
    h('path', { d: 'M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z' }),
  ])
}

function ForumIcon() {
  return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.75, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('path', { d: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2' }),
    h('circle', { cx: 9, cy: 7, r: 4 }),
    h('path', { d: 'M23 21v-2a4 4 0 0 0-3-3.87' }),
    h('path', { d: 'M16 3.13a4 4 0 0 1 0 7.75' }),
  ])
}

function MarketplaceIcon() {
  return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.75, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('path', { d: 'M6 2L3 7v13a2 2 0 002 2h14a2 2 0 002-2V7l-3-5z' }),
    h('line', { x1: 3, y1: 7, x2: 21, y2: 7 }),
    h('path', { d: 'M16 11a4 4 0 01-8 0' }),
  ])
}

function SettingsIcon() {
  return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.75, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('circle', { cx: 12, cy: 12, r: 3 }),
    h('path', { d: 'M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z' }),
  ])
}

function ChevronIcon() {
  return h('svg', { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('path', { d: 'M15 18l-6-6 6-6' }),
  ])
}
</script>

<style scoped>
.side-nav {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--color-sidebar-bg);
  border-right: 1px solid var(--color-sidebar-border);
  display: flex;
  flex-direction: column;
  z-index: 110;
  transition: width 250ms var(--ease-out-expo);
  overflow: hidden;
  box-shadow: 4px 0 16px rgba(0, 0, 0, 0.20);
}

.side-nav.collapsed {
  width: var(--sidebar-collapsed-width);
}

/* ── Header - Premium Logo Area ── */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 14px;
  border-bottom: 1px solid var(--color-sidebar-border);
  min-height: var(--nav-height);
  flex-shrink: 0;
  background: linear-gradient(135deg, var(--color-sidebar-bg) 0%, rgba(30, 90, 168, 0.05) 100%);
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 12px;
  overflow: hidden;
}

.logo-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  overflow: hidden;
  flex-shrink: 0;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  box-shadow: 0 4px 12px rgba(30, 90, 168, 0.30);
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.logo-text {
  font-size: 16px;
  font-weight: 800;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
  white-space: nowrap;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.collapse-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: var(--color-sidebar-hover);
  color: var(--color-text-secondary);
  border-color: var(--color-primary-border);
}


.rotate-180 {
  transform: rotate(180deg);
}

/* ── Navigation - Modern Minimalist ── */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px 8px;
}

.nav-section {
  margin-bottom: 12px;
}

.nav-section-label {
  display: block;
  padding: 10px 12px 6px;
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: 600;
  transition: all var(--transition-normal);
  white-space: nowrap;
  cursor: pointer;
  border: 1px solid transparent;
}

.nav-item:hover {
  background: var(--color-sidebar-hover);
  color: var(--color-text-primary);
  border-color: var(--color-primary-border);
}

.nav-item.active {
  background: var(--color-sidebar-active);
  color: var(--color-accent);
  border-color: var(--color-primary-border);
}

.nav-item-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0;
  background: linear-gradient(180deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border-radius: 0 2px 2px 0;
  transition: height var(--transition-normal);
}

.nav-item.active .nav-item-indicator {
  height: 24px;
}

.nav-item-icon {
  flex-shrink: 0;
  opacity: 0.6;
  font-size: 18px;
}

.nav-item:hover .nav-item-icon,
.nav-item.active .nav-item-icon {
  opacity: 1;
}

.nav-item-label {
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

/* ── Footer - Plan Badge ── */
.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 8px;
  border-top: 1px solid var(--color-sidebar-border);
  flex-shrink: 0;
}

.plan-badge {
  display: block;
  text-align: center;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.08em;
  padding: 7px 12px;
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: all var(--transition-normal);
  cursor: pointer;
}

/* ── FREE: neutral gray ── */
.plan-badge--free {
  color: var(--color-text-muted);
  background: var(--color-primary-bg);
  border: 1px solid var(--color-primary-border);
}

.plan-badge--free:hover {
  color: var(--color-text-secondary);
  border-color: var(--color-primary);
}

/* ── PLUS: teal ── */
.plan-badge--plus {
  color: #1B7A6E;
  background: rgba(27, 122, 110, 0.08);
  border: 1px solid rgba(27, 122, 110, 0.2);
}

.plan-badge--plus:hover {
  background: rgba(27, 122, 110, 0.14);
  border-color: #1B7A6E;
}

/* ── PRO: gold ── */
.plan-badge--pro {
  color: #9A7B3A;
  background: linear-gradient(135deg, rgba(154, 123, 58, 0.08), rgba(201, 169, 98, 0.04));
  border: 1px solid rgba(154, 123, 58, 0.25);
}

.plan-badge--pro:hover {
  background: linear-gradient(135deg, rgba(154, 123, 58, 0.14), rgba(201, 169, 98, 0.08));
  border-color: #9A7B3A;
}

/* ── ULTRA: purple shimmer ── */
.plan-badge--ultra {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.10), rgba(217, 70, 239, 0.06));
  border: 1px solid rgba(139, 92, 246, 0.25);
  background-clip: padding-box;
  color: #8B5CF6;
}

.plan-badge--ultra:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.18), rgba(217, 70, 239, 0.10));
  border-color: #8B5CF6;
}

/* Dark theme */
:root[data-theme="dark"] .plan-badge--plus {
  color: #4DB6AC;
  background: rgba(77, 182, 172, 0.08);
  border-color: rgba(77, 182, 172, 0.2);
}

:root[data-theme="dark"] .plan-badge--plus:hover {
  background: rgba(77, 182, 172, 0.14);
  border-color: #4DB6AC;
}

:root[data-theme="dark"] .plan-badge--pro {
  color: #C9A962;
  background: linear-gradient(135deg, rgba(201, 169, 98, 0.08), rgba(201, 169, 98, 0.03));
  border-color: rgba(201, 169, 98, 0.25);
}

:root[data-theme="dark"] .plan-badge--pro:hover {
  background: linear-gradient(135deg, rgba(201, 169, 98, 0.14), rgba(201, 169, 98, 0.08));
  border-color: #C9A962;
}

:root[data-theme="dark"] .plan-badge--ultra {
  color: #A78BFA;
  background: linear-gradient(135deg, rgba(167, 139, 250, 0.10), rgba(232, 121, 249, 0.06));
  border-color: rgba(167, 139, 250, 0.25);
}

:root[data-theme="dark"] .plan-badge--ultra:hover {
  background: linear-gradient(135deg, rgba(167, 139, 250, 0.18), rgba(232, 121, 249, 0.10));
  border-color: #A78BFA;
}

.footer-collapse-btn {
  width: 100%;
  margin-bottom: 8px;
  padding: 8px;
  justify-content: center;
  border-color: var(--color-border);
}

.footer-collapse-btn:hover {
  background: var(--color-sidebar-hover);
  color: var(--color-text-secondary);
  border-color: var(--color-primary-border);
}

/* ── Transitions ── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 150ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ── Collapsed state ── */
.collapsed .sidebar-header {
  justify-content: center;
  padding: 14px 0;
}

.collapsed .sidebar-nav {
  padding: 8px 6px;
}

.collapsed .nav-item {
  justify-content: center;
  padding: 10px;
}

.collapsed .nav-section-label {
  display: none;
}

.collapsed .sidebar-footer {
  padding: 8px 6px;
}

/* ── Large Screen ── */
@media (min-width: 1920px) {
  .sidebar-header {
    padding: 18px 16px;
  }

  .logo-icon {
    width: 36px;
    height: 36px;
  }

  .logo-text {
    font-size: 17px;
  }

  .nav-item {
    padding: 10px 14px;
    font-size: var(--font-size-md);
    gap: 12px;
  }

  .plan-badge {
    padding: 10px 14px;
  }
}

@media (min-width: 2560px) {
  .sidebar-header {
    padding: 22px 20px;
  }

  .logo-icon {
    width: 44px;
    height: 44px;
  }

  .logo-text {
    font-size: 20px;
  }

  .nav-item {
    padding: 12px 16px;
    font-size: var(--font-size-lg);
    border-radius: var(--radius-lg);
  }

  .nav-section-label {
    font-size: 12px;
    padding: 10px 16px 6px;
  }

  .collapse-btn {
    width: 36px;
    height: 36px;
  }
}

/* ── Tablet ── */
@media (max-width: 1024px) {
  .collapse-btn {
    display: flex;
  }
}

/* ── Mobile ── */
@media (max-width: 768px) {
  .side-nav {
    width: min(var(--sidebar-width), 80vw);
    transform: translateX(-100%);
    transition: transform 250ms var(--ease-out-expo);
  }

  .side-nav:not(.collapsed) {
    transform: translateX(0);
    box-shadow: var(--shadow-xl);
  }

  .side-nav.collapsed {
    width: min(var(--sidebar-width), 80vw);
    transform: translateX(-100%);
  }

  .collapse-btn {
    display: flex;
  }
}
</style>
