<template>
  <header class="top-header">
    <div class="header-content">
      <div class="header-left">
        <button class="mobile-menu-btn" type="button" aria-label="Toggle menu" @click="$emit('toggle-sidebar')">
          <MenuIcon />
        </button>

        <nav class="nav-tabs">
          <RouterLink
            v-for="tab in navTabs"
            :key="tab.path"
            :to="tab.path"
            :class="['nav-tab', { active: isTabActive(tab) }]"
          >
            {{ t(tab.label) }}
          </RouterLink>
        </nav>
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

          <QDropdown
            v-if="userStore.token"
            ref="userDropdownRef"
            :items="userMenuItems"
            @select="handleMenuSelect"
          >
            <template #trigger>
              <button class="user-trigger" type="button">
                <img
                  v-if="profile.avatar_url"
                  :src="profile.avatar_url"
                  :alt="profile.name || 'User avatar'"
                  class="user-avatar user-avatar--image"
                  data-test="topnav-avatar-image"
                />
                <span
                  v-else
                  class="user-avatar"
                  data-test="topnav-avatar-fallback"
                >
                  {{ profile.avatar || '?' }}
                </span>
              </button>
            </template>
            <template #header>
              <div class="dropdown-header">
                <span class="dropdown-name">{{ profile.name || 'User' }}</span>
                <span class="dropdown-email">{{ profile.level }}</span>
              </div>
            </template>
          </QDropdown>
          <button v-else class="user-trigger" type="button" @click="handleAvatarClick">
            <span class="user-avatar user-avatar--guest" data-test="topnav-avatar-fallback">?</span>
          </button>
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
import { QDropdown } from './ui'
import type { DropdownItem } from './ui'

defineEmits<{ 'toggle-sidebar': [] }>()

const route = useRoute()
const { t } = useI18n()
const userStore = useUserStore()
const notificationStore = useNotificationStore()
const { profile } = storeToRefs(userStore)
const notificationCount = computed(() => notificationStore.unreadCount)
const isNotificationPanelOpen = ref(false)
const userDropdownRef = ref<InstanceType<typeof QDropdown> | null>(null)

const userMenuItems = computed<DropdownItem[]>(() => [
  { type: 'divider' },
  { key: 'profile', label: t('common.userProfile'), to: `/users/${profile.value.id}`, icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' },
  { key: 'settings', label: t('common.settings'), to: '/settings', icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>' },
  { type: 'divider' },
  { key: 'logout', label: t('common.logout'), danger: true, icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>' },
])

interface NavTab {
  path: string
  label: string
  matchPrefix?: string
}

const navTabs: NavTab[] = [
  { path: '/', label: 'pageTitle.dashboard' },
  { path: '/strategies', label: 'pageTitle.strategies', matchPrefix: '/strategies' },
  { path: '/backtests', label: 'pageTitle.backtests', matchPrefix: '/backtests' },
  { path: '/bots', label: 'pageTitle.bots', matchPrefix: '/bots' },
  { path: '/marketplace', label: 'pageTitle.marketplace', matchPrefix: '/marketplace' },
]

function isTabActive(tab: NavTab) {
  if (tab.path === '/') return route.path === '/'
  if (tab.matchPrefix) return route.path.startsWith(tab.matchPrefix)
  return route.path === tab.path
}

function handleAvatarClick() {
  window.location.href = '/login'
}

function handleMenuSelect(item: DropdownItem) {
  if (item.key === 'logout') {
    localStorage.removeItem('qyquant-token')
    userStore.$reset()
    window.location.href = '/login'
  }
}

function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
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

// Icons
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

</script>

<style scoped>
.top-header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--nav-height);
  background: var(--color-nav-bg);
  border-bottom: 2px solid var(--color-nav-border);
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
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: color var(--transition-fast), background var(--transition-fast);
}

.mobile-menu-btn:hover {
  color: var(--color-text-primary);
  background: var(--color-surface-hover);
}

/* Pill tab navigation */
.nav-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-tab {
  padding: 6px 16px;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-muted);
  text-decoration: none;
  border: 2px solid transparent;
  border-radius: var(--radius-full);
  transition: color var(--transition-fast), background var(--transition-fast);
}

.nav-tab:hover {
  color: var(--color-text-primary);
  background: var(--color-surface-hover);
}

.nav-tab.active {
  color: #ffffff;
  background: var(--color-primary);
  font-weight: 700;
  border-color: var(--color-border);
}

:root[data-theme="light"] .nav-tab.active {
  color: #ffffff;
  background: var(--color-text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Search */
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
  width: 200px;
  height: 36px;
  padding: 0 40px 0 36px;
  font-size: var(--font-size-sm);
  font-family: var(--font-family);
  font-weight: 500;
  color: var(--color-text-primary);
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-full);
  outline: none;
  transition: border-color var(--transition-fast);
}

.search-input:focus {
  border-color: var(--color-primary);
}

.search-input::placeholder {
  color: var(--color-text-muted);
}

.search-kbd {
  position: absolute;
  right: 10px;
  padding: 2px 6px;
  font-size: var(--font-size-xs);
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--color-text-muted);
  background: var(--color-surface-elevated);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-xs);
  line-height: 1.2;
  pointer-events: none;
}

/* Action buttons */
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
  border: none;
  border-radius: var(--radius-full);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color var(--transition-fast), background var(--transition-fast);
}

.header-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
}

/* Notification dot */
.notification-shell {
  position: relative;
}

.notification-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 7px;
  height: 7px;
  background: var(--color-danger);
  border: 2px solid var(--color-nav-bg);
  border-radius: var(--radius-full);
}

/* User menu */
.user-menu-shell {
  position: relative;
}

.user-trigger {
  display: flex;
  align-items: center;
  padding: 4px;
  background: transparent;
  border: none;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: opacity var(--transition-fast);
}

.user-trigger:hover {
  opacity: 0.85;
}

.user-avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-full);
}

.user-avatar--image {
  object-fit: cover;
}

.user-avatar--guest {
  background: var(--color-surface-active);
  color: var(--color-text-muted);
}

/* Dropdown */
.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 200px;
  padding: 6px;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  z-index: 200;
}

.dropdown-header {
  padding: 10px 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dropdown-name {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.dropdown-email {
  font-size: var(--font-size-xs);
  color: var(--color-primary);
  font-weight: 600;
}

.dropdown-divider {
  height: 1px;
  margin: 4px 0;
  background: var(--color-border);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 12px;
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-decoration: none;
  text-align: left;
  transition: background var(--transition-fast);
}

.dropdown-item:hover {
  background: var(--color-surface-hover);
}

.dropdown-icon {
  color: var(--color-text-muted);
  flex-shrink: 0;
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

/* Large Screen */
@media (min-width: 1920px) {
  .search-input { width: 280px; }
}

@media (min-width: 2560px) {
  .search-input { width: 360px; height: 40px; }
  .header-btn { width: 40px; height: 40px; }
  .user-avatar { width: 36px; height: 36px; }
}

/* Responsive */
@media (max-width: 1024px) {
  .search-input { width: 160px; }
  .nav-tabs { display: none; }
}

@media (max-width: 768px) {
  .mobile-menu-btn { display: flex; }
  .search-box { display: none; }
  .nav-tabs { display: none; }
  .header-content { padding: 0 var(--spacing-md); }
}

@media (max-width: 480px) {
  .header-content { padding: 0 var(--spacing-sm); gap: 8px; }
  .header-actions { gap: 0; }
  .header-btn { width: 32px; height: 32px; }
}
</style>
