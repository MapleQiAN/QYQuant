<template>
  <nav class="top-nav">
    <div class="nav-content">
      <div class="nav-logo">
        <div class="logo-icon">
          <img :src="logoUrl" alt="QY Quant Logo" class="logo-image" />
        </div>
        <div>
          <span class="logo-text">QY Quant</span>
        </div>
      </div>

      <div class="nav-links-shell">
        <div class="nav-links">
          <RouterLink
            v-for="item in navItems"
            :key="item.id"
            :to="item.to"
            :class="['nav-link', { active: route.path === item.to, 'onboarding-highlight': onboardingHighlightTarget === item.target }]"
            :data-onboarding-target="item.target"
          >
            <component :is="getIcon(item.icon)" class="nav-icon" />
            <span>{{ $t(item.label) }}</span>
          </RouterLink>
        </div>
      </div>

      <div class="nav-right">
        <div class="search-box">
          <SearchIcon class="search-icon" />
          <input type="text" :placeholder="$t('common.searchPlaceholder')" class="search-input" />
        </div>
        <div class="nav-actions">
          <button class="nav-btn" type="button" aria-label="鎵撳紑甯姪涓績" @click="userStore.setHelpPanelOpen(true)">
            <HelpIcon />
          </button>

          <div class="notification-shell">
            <button class="nav-btn notification-btn" type="button" aria-label="鎵撳紑閫氱煡涓績" @click="toggleNotifications">
              <BellIcon />
              <span v-if="notificationCount > 0" class="notification-badge">
                {{ notificationCount }}
              </span>
            </button>
            <NotificationPanel v-if="isNotificationPanelOpen" />
          </div>

          <div class="user-avatar">
            <span class="avatar-text">{{ profile.avatar }}</span>
            <span class="user-level">{{ profile.level }}</span>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed, h, onMounted, onUnmounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { RouterLink, useRoute } from 'vue-router'
import NotificationPanel from './NotificationPanel.vue'
import { useNotificationStore } from '../stores/useNotificationStore'
import { useUserStore } from '../stores/user'
import logoUrl from '../logo.png'

const route = useRoute()

const navItems = [
  { id: 'dashboard', to: '/', icon: 'chart', label: 'nav.dashboard', target: null },
  { id: 'strategies', to: '/strategies', icon: 'target', label: 'common.newStrategy', target: 'strategy-library-entry' },
  { id: 'backtests', to: '/backtests', icon: 'chart', label: 'nav.backtests', target: null },
  { id: 'bots', to: '/bots', icon: 'robot', label: 'nav.bots', target: null },
  { id: 'forum', to: '/forum', icon: 'users', label: 'nav.forum', target: null },
]

const userStore = useUserStore()
const notificationStore = useNotificationStore()
const { profile, onboardingHighlightTarget } = storeToRefs(userStore)
const notificationCount = computed(() => notificationStore.unreadCount)
const isNotificationPanelOpen = ref(false)

onMounted(() => {
  notificationStore.startPolling()
})

onUnmounted(() => {
  notificationStore.stopPolling()
})

function toggleNotifications() {
  isNotificationPanelOpen.value = !isNotificationPanelOpen.value
}

const ChartIcon = () => h('svg', {
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M3 3v18h18' }),
  h('path', { d: 'M18 17V9' }),
  h('path', { d: 'M13 17V5' }),
  h('path', { d: 'M8 17v-3' })
])

const RobotIcon = () => h('svg', {
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('rect', { x: 3, y: 11, width: 18, height: 10, rx: 2 }),
  h('circle', { cx: 12, cy: 5, r: 2 }),
  h('path', { d: 'M12 7v4' }),
  h('line', { x1: 8, y1: 16, x2: 8, y2: 16 }),
  h('line', { x1: 16, y1: 16, x2: 16, y2: 16 })
])

const UsersIcon = () => h('svg', {
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2' }),
  h('circle', { cx: 9, cy: 7, r: 4 }),
  h('path', { d: 'M23 21v-2a4 4 0 0 0-3-3.87' }),
  h('path', { d: 'M16 3.13a4 4 0 0 1 0 7.75' })
])

const HelpIcon = () => h('svg', {
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 12, cy: 12, r: 10 }),
  h('path', { d: 'M9.09 9a3 3 0 1 1 5.82 1c0 2-3 2-3 4' }),
  h('line', { x1: 12, y1: 17, x2: 12.01, y2: 17 }),
])

const SearchIcon = () => h('svg', {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 11, cy: 11, r: 8 }),
  h('path', { d: 'm21 21-4.3-4.3' })
])

const BellIcon = () => h('svg', {
  width: 20,
  height: 20,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9' }),
  h('path', { d: 'M10.3 21a1.94 1.94 0 0 0 3.4 0' })
])

const TargetIcon = () => h('svg', {
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 2,
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 12, cy: 12, r: 10 }),
  h('circle', { cx: 12, cy: 12, r: 6 }),
  h('circle', { cx: 12, cy: 12, r: 2 }),
])

const iconMap: Record<string, any> = {
  chart: ChartIcon,
  target: TargetIcon,
  robot: RobotIcon,
  users: UsersIcon
}

function getIcon(iconName: string) {
  return iconMap[iconName] || ChartIcon
}
</script>

<style scoped>
.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 250, 252, 0.86));
  backdrop-filter: var(--glass-backdrop);
  -webkit-backdrop-filter: var(--glass-backdrop);
  border-bottom: 1px solid rgba(203, 213, 225, 0.8);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.nav-content {
  max-width: var(--container-max-width);
  margin: 0 auto;
  padding: 12px var(--spacing-lg);
  display: flex;
  align-items: center;
  gap: 18px;
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 172px;
}

.logo-icon {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(241, 245, 249, 0.92));
  border: 1px solid rgba(203, 213, 225, 0.9);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.logo-text {
  font-size: 17px;
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  line-height: 1.1;
  letter-spacing: 0.01em;
}

.nav-links-shell {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
  padding: 4px;
  border-radius: 14px;
  background: rgba(148, 163, 184, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 38px;
  padding: 8px 12px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: #475569;
  border: 1px solid transparent;
  border-radius: 10px;
  transition:
    color var(--transition-fast),
    background-color var(--transition-fast),
    border-color var(--transition-fast),
    box-shadow var(--transition-fast);
  text-decoration: none;
  white-space: nowrap;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.72);
  border-color: rgba(226, 232, 240, 0.95);
  color: var(--color-text-primary);
}

.nav-link.active {
  background: linear-gradient(180deg, rgba(238, 242, 255, 0.95), rgba(224, 231, 255, 0.86));
  border-color: rgba(165, 180, 252, 0.55);
  color: #4338ca;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}

.nav-icon {
  opacity: 0.72;
  flex-shrink: 0;
}

.nav-link:hover .nav-icon,
.nav-link.active .nav-icon {
  opacity: 1;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
  flex-shrink: 0;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: var(--color-text-muted);
  pointer-events: none;
}

.search-input {
  width: 240px;
  height: 40px;
  padding: 0 14px 0 38px;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  background: rgba(248, 250, 252, 0.92);
  border: 1px solid rgba(203, 213, 225, 0.95);
  border-radius: 12px;
  outline: none;
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast),
    background-color var(--transition-fast);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.82);
}

.search-input:focus {
  background: rgba(255, 255, 255, 0.98);
  border-color: rgba(129, 140, 248, 0.72);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.search-input::placeholder {
  color: var(--color-text-muted);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-btn {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(248, 250, 252, 0.92);
  border: 1px solid rgba(203, 213, 225, 0.95);
  border-radius: 11px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition:
    color var(--transition-fast),
    border-color var(--transition-fast),
    background-color var(--transition-fast),
    box-shadow var(--transition-fast);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.82);
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.98);
  border-color: rgba(165, 180, 252, 0.42);
  color: var(--color-primary-dark);
}

.nav-btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}

.notification-shell {
  position: relative;
}

.notification-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 17px;
  height: 17px;
  padding: 0 4px;
  font-size: 10px;
  font-weight: var(--font-weight-semibold);
  background: var(--color-danger);
  color: var(--color-text-inverse);
  border: 2px solid rgba(255, 255, 255, 0.95);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.user-avatar {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 4px 10px 4px 4px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.92));
  border: 1px solid rgba(203, 213, 225, 0.95);
  border-radius: 12px;
  cursor: pointer;
  transition:
    border-color var(--transition-fast),
    background-color var(--transition-fast),
    box-shadow var(--transition-fast);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

.user-avatar:hover {
  background: rgba(255, 255, 255, 0.98);
  border-color: rgba(165, 180, 252, 0.4);
}

.avatar-text {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: var(--font-weight-semibold);
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  color: var(--color-text-inverse);
  border-radius: 9px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.user-level {
  font-size: 11px;
  font-weight: var(--font-weight-semibold);
  color: #4338ca;
  background: rgba(238, 242, 255, 0.88);
  padding: 3px 8px;
  border-radius: 999px;
  letter-spacing: 0.03em;
}

@media (max-width: 1024px) {
  .nav-content {
    gap: 14px;
    padding: 10px var(--spacing-lg);
  }

  .nav-logo {
    min-width: 156px;
  }

  .nav-link {
    padding: 8px 10px;
  }

  .search-input {
    width: 180px;
  }
}

@media (max-width: 900px) {
  .nav-content {
    flex-wrap: wrap;
  }

  .nav-links-shell {
    order: 3;
    flex-basis: 100%;
  }

  .nav-right {
    margin-left: auto;
  }

  .search-input {
    width: 160px;
  }
}

@media (max-width: 768px) {
  .nav-content {
    padding: 10px var(--spacing-md);
  }

  .nav-logo {
    min-width: auto;
  }

  .nav-links {
    overflow-x: auto;
    scrollbar-width: none;
  }

  .nav-links::-webkit-scrollbar {
    display: none;
  }

  .nav-right {
    width: 100%;
    justify-content: space-between;
    margin-left: 0;
  }

  .search-box {
    flex: 1;
  }

  .search-input {
    width: 100%;
  }
}
</style>
