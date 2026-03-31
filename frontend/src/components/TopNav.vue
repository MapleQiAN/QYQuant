<template>
  <header class="top-header">
    <div class="header-content">
      <div class="header-left">
        <button class="mobile-menu-btn" type="button" aria-label="Toggle menu" @click="$emit('toggle-sidebar')">
          <MenuIcon />
        </button>
        <div class="breadcrumb">
          <span class="breadcrumb-current">{{ currentPageTitle }}</span>
        </div>
      </div>

      <div class="header-right">
        <div class="search-box">
          <SearchIcon class="search-icon" />
          <input type="text" :placeholder="$t('common.searchPlaceholder')" class="search-input" />
          <kbd class="search-kbd">/</kbd>
        </div>

        <div class="header-actions">
          <button class="header-btn" type="button" :aria-label="userStore.theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'" @click="userStore.toggleTheme()">
            <MoonIcon v-if="userStore.theme === 'light'" />
            <SunIcon v-else />
          </button>

          <button class="header-btn" type="button" aria-label="Help" @click="userStore.setHelpPanelOpen(true)">
            <HelpIcon />
          </button>

          <div class="notification-shell">
            <button class="header-btn" type="button" aria-label="Notifications" @click="toggleNotifications">
              <BellIcon />
              <span v-if="notificationCount > 0" class="notification-dot" />
            </button>
            <NotificationPanel v-if="isNotificationPanelOpen" />
          </div>

          <div class="divider-v" />

          <div class="user-menu-shell">
            <button class="user-trigger" type="button" @click="handleAvatarClick">
              <img
                v-if="userStore.token && profile.avatar_url"
                :src="profile.avatar_url"
                :alt="profile.name || 'User avatar'"
                class="user-avatar user-avatar--image"
                data-test="topnav-avatar-image"
              />
              <span
                v-else
                class="user-avatar"
                :class="{ 'user-avatar--guest': !userStore.token }"
                data-test="topnav-avatar-fallback"
              >
                {{ userStore.token ? profile.avatar : '?' }}
              </span>
              <span class="user-name">{{ userStore.token ? (profile.name || '') : t('common.notLoggedIn') }}</span>
              <ChevronDownIcon />
            </button>
            <div v-if="isUserMenuOpen" class="user-dropdown">
              <div class="dropdown-header">
                <span class="dropdown-name">{{ profile.name || 'User' }}</span>
                <span class="dropdown-email">{{ profile.level }}</span>
              </div>
              <div class="dropdown-divider" />
              <RouterLink class="dropdown-item" :to="`/users/${profile.id}`" @click="isUserMenuOpen = false">
                <UserIcon class="dropdown-icon" />
                {{ $t('common.userProfile') }}
              </RouterLink>
              <RouterLink class="dropdown-item" to="/settings" @click="isUserMenuOpen = false">
                <SettingsSmIcon class="dropdown-icon" />
                {{ $t('common.settings') }}
              </RouterLink>
              <div class="dropdown-divider" />
              <button class="dropdown-item danger" type="button" @click="handleLogout">
                <LogoutIcon class="dropdown-icon" />
                {{ $t('common.logout') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, h, onMounted, onUnmounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { RouterLink, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import NotificationPanel from './NotificationPanel.vue'
import { useNotificationStore } from '../stores/useNotificationStore'
import { useUserStore } from '../stores/user'

defineEmits<{ 'toggle-sidebar': [] }>()

const route = useRoute()
const { t } = useI18n()
const userStore = useUserStore()
const notificationStore = useNotificationStore()
const { profile } = storeToRefs(userStore)
const notificationCount = computed(() => notificationStore.unreadCount)
const isNotificationPanelOpen = ref(false)
const isUserMenuOpen = ref(false)

const pageTitles: Record<string, string> = {
  '/': 'pageTitle.dashboard',
  '/learn': 'pageTitle.learn',
  '/strategies': 'pageTitle.strategies',
  '/backtests': 'pageTitle.backtests',
  '/bots': 'pageTitle.bots',
  '/forum': 'pageTitle.forum',
  '/marketplace': 'pageTitle.marketplace',
  '/settings': 'pageTitle.settings',
  '/pricing': 'pageTitle.pricing',
}

const currentPageTitle = computed(() => {
  for (const [path, key] of Object.entries(pageTitles)) {
    if (path === '/' && route.path === '/') return t(key)
    if (path !== '/' && route.path.startsWith(path)) return t(key)
  }
  return t('pageTitle.default')
})

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
  if (!target.closest('.user-menu-shell')) {
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

// ── Icons ──
const MenuIcon = () => h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
  h('line', { x1: 3, y1: 6, x2: 21, y2: 6 }),
  h('line', { x1: 3, y1: 12, x2: 21, y2: 12 }),
  h('line', { x1: 3, y1: 18, x2: 21, y2: 18 }),
])

const SearchIcon = () => h('svg', { width: 14, height: 14, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
  h('circle', { cx: 11, cy: 11, r: 8 }),
  h('path', { d: 'm21 21-4.3-4.3' }),
])

const BellIcon = () => h('svg', { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
  h('path', { d: 'M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9' }),
  h('path', { d: 'M10.3 21a1.94 1.94 0 0 0 3.4 0' }),
])

const SunIcon = () => h('svg', { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
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

const MoonIcon = () => h('svg', { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
  h('path', { d: 'M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z' }),
])

const HelpIcon = () => h('svg', { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
  h('circle', { cx: 12, cy: 12, r: 10 }),
  h('path', { d: 'M9.09 9a3 3 0 1 1 5.82 1c0 2-3 2-3 4' }),
  h('line', { x1: 12, y1: 17, x2: 12.01, y2: 17 }),
])

const ChevronDownIcon = () => h('svg', { width: 12, height: 12, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
  h('path', { d: 'M6 9l6 6 6-6' }),
])

const UserIcon = () => h('svg', { width: 14, height: 14, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
  h('path', { d: 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2' }),
  h('circle', { cx: 12, cy: 7, r: 4 }),
])

const SettingsSmIcon = () => h('svg', { width: 14, height: 14, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
  h('circle', { cx: 12, cy: 12, r: 3 }),
  h('path', { d: 'M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z' }),
])

const LogoutIcon = () => h('svg', { width: 14, height: 14, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
  h('path', { d: 'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4' }),
  h('polyline', { points: '16 17 21 12 16 7' }),
  h('line', { x1: 21, y1: 12, x2: 9, y2: 12 }),
])
</script>

<style scoped>
.top-header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--nav-height);
  background: var(--color-nav-bg);
  border-bottom: 1px solid var(--color-nav-border);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.header-content {
  height: 100%;
  padding: 0 var(--spacing-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.mobile-menu-btn {
  display: none;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mobile-menu-btn:hover {
  border-color: var(--color-primary-border);
  color: var(--color-text-primary);
}

.breadcrumb-current {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ── Search - Modern ── */
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
  width: 220px;
  height: 36px;
  padding: 0 40px 0 36px;
  font-size: var(--font-size-sm);
  font-family: var(--font-family);
  font-weight: 500;
  color: var(--color-text-primary);
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  outline: none;
  transition: all var(--transition-fast);
}

.search-input:focus {
  border-color: var(--color-primary-border);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
  background: var(--color-surface);
}

.search-input::placeholder {
  color: var(--color-text-muted);
}

.search-kbd {
  position: absolute;
  right: 10px;
  padding: 2px 6px;
  font-size: 10px;
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-text-muted);
  background: var(--color-surface-active);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  line-height: 1.2;
  pointer-events: none;
  letter-spacing: 0.02em;
}

/* ── Action buttons - Premium ── */
.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.header-btn {
  position: relative;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.header-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
  border-color: var(--color-primary-border);
}

.divider-v {
  width: 1px;
  height: 24px;
  background: var(--color-border);
  margin: 0 6px;
}

/* ── Notifications - Live Indicator ── */
.notification-shell {
  position: relative;
}

.notification-dot {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 8px;
  height: 8px;
  background: var(--color-danger);
  border: 2px solid var(--color-nav-bg);
  border-radius: var(--radius-full);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 59, 59, 0.4); }
  50% { box-shadow: 0 0 0 4px rgba(255, 59, 59, 0.1); }
}

/* ── User Menu - Premium ── */
.user-menu-shell {
  position: relative;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px 6px 6px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.user-trigger:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-primary-border);
}

.user-avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: #fff;
  border-radius: var(--radius-md);
  box-shadow: 0 2px 8px rgba(30, 90, 168, 0.25);
}

.user-avatar--image {
  object-fit: cover;
}

.user-avatar--guest {
  background: var(--color-surface-active);
  color: var(--color-text-muted);
  box-shadow: none;
  border: 1px solid var(--color-border);
}

.user-name {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-trigger svg {
  color: var(--color-text-muted);
  width: 14px;
  height: 14px;
  transition: transform var(--transition-fast);
}

/* ── Dropdown Menu - Glass Style ── */
.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 220px;
  padding: 6px;
  background: var(--glass-background);
  backdrop-filter: var(--glass-backdrop);
  -webkit-backdrop-filter: var(--glass-backdrop);
  border: var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  z-index: 200;
}

.dropdown-header {
  padding: 12px 14px 10px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.dropdown-name {
  font-size: var(--font-size-sm);
  font-weight: 700;
  color: var(--color-text-primary);
}

.dropdown-email {
  font-size: var(--font-size-xs);
  color: var(--color-accent);
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.dropdown-divider {
  height: 1px;
  margin: 6px 0;
  background: var(--color-border);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 12px;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  text-decoration: none;
  text-align: left;
  transition: all var(--transition-fast);
}

.dropdown-item:hover {
  background: var(--color-surface-hover);
  color: var(--color-accent);
}

.dropdown-icon {
  color: var(--color-text-muted);
  flex-shrink: 0;
  width: 14px;
  height: 14px;
}

.dropdown-item.danger {
  color: var(--color-danger);
}

.dropdown-item.danger .dropdown-icon {
  color: var(--color-danger);
}

.dropdown-item.danger:hover {
  background: var(--color-danger-bg);
}

/* ── Large Screen ── */
@media (min-width: 1920px) {
  .search-input {
    width: 320px;
    height: 36px;
    font-size: var(--font-size-md);
  }

  .header-btn {
    width: 36px;
    height: 36px;
  }

  .user-avatar {
    width: 34px;
    height: 34px;
  }
}

@media (min-width: 2560px) {
  .search-input {
    width: 400px;
    height: 40px;
  }

  .header-btn {
    width: 40px;
    height: 40px;
  }

  .user-avatar {
    width: 38px;
    height: 38px;
  }

  .user-name {
    font-size: var(--font-size-md);
    max-width: 160px;
  }

  .divider-v {
    height: 28px;
  }
}

/* ── Responsive ── */
@media (max-width: 1024px) {
  .search-input {
    width: 160px;
  }
}

@media (max-width: 768px) {
  .mobile-menu-btn {
    display: flex;
  }

  .search-box {
    display: none;
  }

  .user-name {
    display: none;
  }

  .header-content {
    padding: 0 var(--spacing-md);
  }

  .divider-v {
    margin: 0 2px;
  }
}

@media (max-width: 480px) {
  .header-content {
    padding: 0 var(--spacing-sm);
    gap: 8px;
  }

  .header-actions {
    gap: 0;
  }

  .header-btn {
    width: 28px;
    height: 28px;
  }

  .breadcrumb-current {
    font-size: var(--font-size-md);
  }
}
</style>
