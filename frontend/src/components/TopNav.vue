<template>
  <nav class="top-nav">
    <div class="nav-content">
      <div class="nav-logo">
        <div class="logo-icon">
          <img :src="logoUrl" alt="QY Quant Logo" class="logo-image" />
        </div>
        <span class="logo-text">QY Quant</span>
      </div>

      <div class="nav-links">
        <RouterLink
          v-for="item in navItems"
          :key="item.id"
          :to="item.to"
          :class="['nav-link', { active: route.path === item.to }]"
        >
          <component :is="getIcon(item.icon)" class="nav-icon" />
          <span>{{ $t(item.label) }}</span>
        </RouterLink>
      </div>

      <div class="nav-right">
        <div class="search-box">
          <SearchIcon class="search-icon" />
          <input type="text" :placeholder="$t('common.searchPlaceholder')" class="search-input" />
        </div>

        <button class="nav-btn notification-btn">
          <BellIcon />
          <span v-if="profile.notifications > 0" class="notification-badge">
            {{ profile.notifications }}
          </span>
        </button>

        <div class="user-avatar">
          <span class="avatar-text">{{ profile.avatar }}</span>
          <span class="user-level">{{ profile.level }}</span>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { h } from 'vue'
import { storeToRefs } from 'pinia'
import { RouterLink, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import logoUrl from '../logo.png'

const route = useRoute()

const navItems = [
  { id: 'dashboard', to: '/', icon: 'chart', label: 'nav.dashboard' },
  { id: 'backtests', to: '/backtests', icon: 'chart', label: 'nav.backtests' },
  { id: 'bots', to: '/bots', icon: 'robot', label: 'nav.bots' },
  { id: 'forum', to: '/forum', icon: 'users', label: 'nav.forum' }
]

const userStore = useUserStore()
const { profile } = storeToRefs(userStore)

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

const iconMap: Record<string, any> = {
  chart: ChartIcon,
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
  background: var(--glass-background);
  backdrop-filter: var(--glass-backdrop);
  -webkit-backdrop-filter: var(--glass-backdrop);
  border-bottom: 1px solid var(--color-border-light);
}

.nav-content {
  max-width: var(--container-max-width);
  margin: 0 auto;
  padding: var(--spacing-md) var(--spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--spacing-xl);
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.logo-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.logo-text {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  text-decoration: none;
}

.nav-link:hover {
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

.nav-link.active {
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

.nav-icon {
  opacity: 0.8;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-left: auto;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: var(--spacing-md);
  color: var(--color-text-muted);
  pointer-events: none;
}

.search-input {
  width: 240px;
  padding: var(--spacing-sm) var(--spacing-md);
  padding-left: 40px;
  font-size: var(--font-size-sm);
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  outline: none;
  transition: all var(--transition-fast);
}

.search-input:focus {
  border-color: var(--color-primary-light);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.search-input::placeholder {
  color: var(--color-text-muted);
}

.nav-btn {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.nav-btn:hover {
  background: var(--color-background);
  color: var(--color-primary);
}

.notification-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  font-size: 11px;
  font-weight: var(--font-weight-semibold);
  background: var(--color-danger);
  color: var(--color-text-inverse);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-avatar {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs);
  padding-right: var(--spacing-md);
  background: var(--color-background);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.user-avatar:hover {
  background: var(--color-border-light);
}

.avatar-text {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  color: var(--color-text-inverse);
  border-radius: var(--radius-full);
}

.user-level {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
  background: var(--color-primary-bg);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}
</style>
