<template>
  <section class="settings-view">
    <div class="container">
      <h1 class="view-title">{{ $t('settings.title') }}</h1>
      <div class="card setting-card">
        <div class="setting-header">
          <div>
            <h3>{{ $t('settings.language') }}</h3>
            <p class="hint">{{ $t('settings.languageHint') }}</p>
          </div>
          <div class="toggle">
            <button
              class="toggle-btn"
              :class="{ active: locale === 'zh' }"
              data-locale="zh"
              type="button"
              @click="setLocale('zh')"
            >
              {{ $t('settings.zh') }}
            </button>
            <button
              class="toggle-btn"
              :class="{ active: locale === 'en' }"
              data-locale="en"
              type="button"
              @click="setLocale('en')"
            >
              {{ $t('settings.en') }}
            </button>
          </div>
        </div>
      </div>
      <div class="card setting-card">
        <div class="setting-header">
          <div>
            <h3>{{ $t('settings.marketStyle') }}</h3>
            <p class="hint">{{ $t('settings.marketStyleHint') }}</p>
          </div>
          <div class="toggle">
            <button
              class="toggle-btn"
              :class="{ active: marketStyle === 'cn' }"
              data-market-style="cn"
              type="button"
              @click="setMarketStyle('cn')"
            >
              {{ $t('settings.marketStyleCn') }}
            </button>
            <button
              class="toggle-btn"
              :class="{ active: marketStyle === 'us' }"
              data-market-style="us"
              type="button"
              @click="setMarketStyle('us')"
            >
              {{ $t('settings.marketStyleUs') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const { locale, marketStyle } = storeToRefs(userStore)

function setLocale(next: 'en' | 'zh') {
  userStore.setLocale(next)
}

function setMarketStyle(next: 'cn' | 'us') {
  userStore.setMarketStyle(next)
}
</script>

<style scoped>
.settings-view {
  width: 100%;
}

.view-title {
  margin: 0 0 var(--spacing-lg);
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.setting-card {
  padding: var(--spacing-lg);
}

.setting-card + .setting-card {
  margin-top: var(--spacing-md);
}

.setting-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-xl);
}

.hint {
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.toggle {
  display: inline-flex;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.toggle-btn {
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  padding: var(--spacing-xs) var(--spacing-md);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toggle-btn:hover {
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

.toggle-btn.active {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}
</style>
