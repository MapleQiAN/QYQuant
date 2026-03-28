<template>
  <nav class="sidebar-nav">
    <!-- Logo -->
    <div class="nav-logo">
      <img :src="logoUrl" alt="QY Quant" class="logo-image" />
    </div>

    <!-- Main nav links -->
    <div class="nav-links">
      <RouterLink
        v-for="item in navItems"
        :key="item.id"
        :to="item.to"
        :class="['nav-link', { active: isActive(item.to) }]"
        :data-onboarding-target="item.target"
        :title="$t(item.label)"
      >
        <component :is="getIcon(item.icon)" class="nav-icon" />
        <span class="nav-tooltip">{{ $t(item.label) }}</span>
      </RouterLink>
    </div>

    <!-- Bottom actions -->
    <div class="nav-bottom">
      <button
        class="nav-link"
        type="button"
        :title="$t('common.searchPlaceholder')"
        @click="$emit('open-search')"
      >
        <SearchIcon class="nav-icon" />
        <span class="nav-tooltip">{{ $t('common.searchPlaceholder') }}</span>
      </button>

      <button
        class="nav-link"
        type="button"
        :title="userStore.theme === 'dark' ? '浅色模式' : '深色模式'"
        @click="userStore.toggleTheme()"
      >
        <MoonIcon v-if="userStore.theme === 'light'" class="nav-icon" />
        <SunIcon v-else class="nav-icon" />
      </button>

      <button
        class="nav-link"
        type="button"
        title="帮助"
        @click="userStore.setHelpPanelOpen(true)"
      >
        <HelpIcon class="nav-icon" />
      </button>

      <div class="notification-shell">
        <button
          class="nav-link"
          type="button"
          title="通知"
          @click="toggleNotifications"
        >
          <BellIcon class="nav-icon" />
          <span v-if="notificationCount > 0" class="notification-badge">
            {{ notificationCount }}
          </span>
        </button>
        <NotificationPanel v-if="isNotificationPanelOpen" class="notification-dropdown" />
      </div>

      <div class="user-shell">
        <button class="user-avatar" type="button" @click="handleAvatarClick" :title="profile.name || '用户'">
          <span class="avatar-text">{{ profile.avatar }}</span>
        </button>
        <div v-if="isUserMenuOpen" class="user-dropdown">
          <RouterLink class="dropdown-item" :to="`/users/${profile.id}`" @click="isUserMenuOpen = false">
            个人主页
          </RouterLink>
          <RouterLink class="dropdown-item" to="/settings" @click="isUserMenuOpen = false">
            设置
          </RouterLink>
          <button class="dropdown-item danger" type="button" @click="handleLogout">
            退出登录
          </button>
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

defineEmits<{ 'open-search': [] }>()

const route = useRoute()

const navItems = [
  { id: 'dashboard', to: '/', icon: 'chart', label: 'nav.dashboard', target: null },
  { id: 'strategies', to: '/strategies', icon: 'target', label: 'common.newStrategy', target: 'strategy-library-entry' },
  { id: 'backtests', to: '/backtests', icon: 'activity', label: 'nav.backtests', target: null },
  { id: 'bots', to: '/bots', icon: 'robot', label: 'nav.bots', target: null },
  { id: 'marketplace', to: '/marketplace', icon: 'store', label: 'nav.marketplace', target: null },
  { id: 'forum', to: '/forum', icon: 'users', label: 'nav.forum', target: null },
]

const userStore = useUserStore()
const notificationStore = useNotificationStore()
const { profile } = storeToRefs(userStore)
const notificationCount = computed(() => notificationStore.unreadCount)
const isNotificationPanelOpen = ref(false)
const isUserMenuOpen = ref(false)

function isActive(to: string) {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to)
}

function handleAvatarClick() {
  if (!userStore.token) {
    window.location.href = '/login'
    return
  }
  isUserMenuOpen.value = !isUserMenuOpen.value
}

function handleLogout() {
  isUserMenuOpen.value = false
  localStorage.removeItem('qyquant-token')
  window.location.href = '/login'
}

function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.user-shell')) {
    isUserMenuOpen.value = false
  }
  if (!target.closest('.notification-shell')) {
    isNotificationPanelOpen.value = false
  }
}

onMounted(() => {
  notificationStore.startPolling()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  notificationStore.stopPolling()
  document.removeEventListener('click', handleClickOutside)
})

function toggleNotifications() {
  isNotificationPanelOpen.value = !isNotificationPanelOpen.value
}

/* ── Icons (16x16 stroke:1.5) ── */
const ChartIcon = () => h('svg', {
  width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M3 3v18h18' }),
  h('path', { d: 'M18 17V9' }),
  h('path', { d: 'M13 17V5' }),
  h('path', { d: 'M8 17v-3' })
])

const ActivityIcon = () => h('svg', {
  width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
}, [
  h('polyline', { points: '22 12 18 12 15 21 9 3 6 12 2 12' })
])

const RobotIcon = () => h('svg', {
  width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
}, [
  h('rect', { x: 3, y: 11, width: 18, height: 10, rx: 2 }),
  h('circle', { cx: 12, cy: 5, r: 2 }),
  h('path', { d: 'M12 7v4' }),
  h('line', { x1: 8, y1: 16, x2: 8, y2: 16 }),
  h('line', { x1: 16, y1: 16, x2: 16, y2: 16 })
])

const UsersIcon = () => h('svg', {
  width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2' }),
  h('circle', { cx: 9, cy: 7, r: 4 }),
  h('path', { d: 'M23 21v-2a4 4 0 0 0-3-3.87' }),
  h('path', { d: 'M16 3.13a4 4 0 0 1 0 7.75' })
])

const TargetIcon = () => h('svg', {
  width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 12, cy: 12, r: 10 }),
  h('circle', { cx: 12, cy: 12, r: 6 }),
  h('circle', { cx: 12, cy: 12, r: 2 }),
])

const StoreIcon = () => h('svg', {
  width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z' }),
  h('polyline', { points: '9 22 9 12 15 12 15 22' })
])

const HelpIcon = () => h('svg', {
  width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 12, cy: 12, r: 10 }),
  h('path', { d: 'M9.09 9a3 3 0 1 1 5.82 1c0 2-3 2-3 4' }),
  h('line', { x1: 12, y1: 17, x2: 12.01, y2: 17 }),
])

const SearchIcon = () => h('svg', {
  width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 11, cy: 11, r: 8 }),
  h('path', { d: 'm21 21-4.3-4.3' })
])

const BellIcon = () => h('svg', {
  width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9' }),
  h('path', { d: 'M10.3 21a1.94 1.94 0 0 0 3.4 0' })
])

const SunIcon = () => h('svg', {
  width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
}, [
  h('circle', { cx: 12, cy: 12, r: 5 }),
  h('line', { x1: 12, y1: 1, x2: 12, y2: 3 }),
  h('line', { x1: 12, y1: 21, x2: 12, y2: 23 }),
  h('line', { x1: 4.22, y1: 4.22, x2: 5.64, y2: 5.64 }),
  h('line', { x1: 18.36, y1: 18.36, x2: 19.78, y2: 19.78 }),
  h('line', { x1: 1, y1: 12, x2: 3, y2: 12 }),
  h('line', { x1: 21, y1: 12, x2: 23, y2: 12 }),
  h('line', { x1: 4.22, y1: 19.78, x2: 5.64, y2: 18.36 }),
  h('line', { x1: 18.36, y1: 5.64, x2: 19.78, y2: 4.22 }),
])

const MoonIcon = () => h('svg', {
  width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z' }),
])

const iconMap: Record<string, any> = {
  chart: ChartIcon,
  activity: ActivityIcon,
  target: TargetIcon,
  robot: RobotIcon,
  users: UsersIcon,
  store: StoreIcon,
}

function getIcon(iconName: string) {
  return iconMap[iconName] || ChartIcon
}
</script>

<style scoped>
.sidebar-nav {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--color-nav-bg);
  border-right: 1px solid var(--color-nav-border);
  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow: hidden;
}

/* Logo */
.nav-logo {
  width: var(--sidebar-width);
  height: var(--sidebar-width);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-bottom: 1px solid var(--color-border);
}

.logo-image {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

/* Nav links */
.nav-links {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: var(--spacing-xs) 0;
  gap: 2px;
  overflow-y: auto;
}

.nav-link {
  position: relative;
  width: var(--sidebar-width);
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  text-decoration: none;
  background: none;
  border: none;
  cursor: pointer;
  transition: color var(--transition-fast), background var(--transition-fast);
  flex-shrink: 0;
}

.nav-link:hover {
  color: var(--color-text-primary);
  background: var(--color-surface-hover);
}

.nav-link.active {
  color: var(--color-primary-light);
}

.nav-link.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: var(--color-primary);
  border-radius: 0 1px 1px 0;
}

.nav-icon {
  flex-shrink: 0;
}

/* Tooltip on hover */
.nav-tooltip {
  position: absolute;
  left: calc(var(--sidebar-width) + 8px);
  padding: 4px 8px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-family: var(--font-family);
  color: var(--color-text-primary);
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--transition-fast);
  z-index: 200;
}

.nav-link:hover .nav-tooltip {
  opacity: 1;
}

/* Bottom section */
.nav-bottom {
  display: flex;
  flex-direction: column;
  padding: var(--spacing-xs) 0;
  gap: 2px;
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
}

/* Notification */
.notification-shell {
  position: relative;
}

.notification-badge {
  position: absolute;
  top: 6px;
  right: 8px;
  min-width: 14px;
  height: 14px;
  padding: 0 3px;
  font-size: 9px;
  font-weight: var(--font-weight-bold);
  background: var(--color-danger);
  color: #fff;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.notification-dropdown {
  position: fixed;
  left: calc(var(--sidebar-width) + 4px);
  bottom: 60px;
  z-index: 200;
}

/* User avatar */
.user-shell {
  position: relative;
  display: flex;
  justify-content: center;
  padding: var(--spacing-xs) 0;
}

.user-avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: border-color var(--transition-fast);
}

.user-avatar:hover {
  border-color: var(--color-border-hover);
}

.avatar-text {
  font-size: 11px;
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
}

.user-dropdown {
  position: fixed;
  left: calc(var(--sidebar-width) + 4px);
  bottom: 8px;
  min-width: 140px;
  padding: 4px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: 200;
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 6px 10px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-decoration: none;
  text-align: left;
  transition: background-color var(--transition-fast);
}

.dropdown-item:hover {
  background: var(--color-surface-hover);
}

.dropdown-item.danger {
  color: var(--color-danger);
}

.dropdown-item.danger:hover {
  background: var(--color-danger-bg);
}

/* ── Mobile: collapse to bottom bar ── */
@media (max-width: 768px) {
  .sidebar-nav {
    position: fixed;
    left: 0;
    right: 0;
    top: auto;
    bottom: 0;
    width: 100%;
    height: var(--sidebar-width);
    flex-direction: row;
    border-right: none;
    border-top: 1px solid var(--color-nav-border);
  }

  .nav-logo {
    display: none;
  }

  .nav-links {
    flex-direction: row;
    flex: 1;
    justify-content: space-around;
    padding: 0;
    gap: 0;
  }

  .nav-link {
    width: auto;
    flex: 1;
    height: var(--sidebar-width);
  }

  .nav-link.active::before {
    left: 25%;
    right: 25%;
    top: 0;
    bottom: auto;
    width: auto;
    height: 2px;
    border-radius: 0 0 1px 1px;
  }

  .nav-tooltip {
    display: none;
  }

  .nav-bottom {
    display: none;
  }
}
</style>
