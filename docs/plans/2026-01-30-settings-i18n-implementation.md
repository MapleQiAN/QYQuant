# Settings Page + i18n v11 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move the locale switcher into a Settings page and upgrade vue-i18n to v11 while keeping all UI text localized.

**Architecture:** Add a `/settings` route with a Settings view that reads/writes `useUserStore().locale`, which also updates vue-i18n global locale. Remove the language toggle from TopNav and route the Dashboard "Settings" button to `/settings`.

**Tech Stack:** Vue 3, Pinia, Vue Router, Vue I18n v11, Vitest, @vue/test-utils.

---

### Task 1: Settings view + i18n messages (TDD)

**Files:**
- Create: `frontend/src/views/SettingsView.test.ts`
- Create: `frontend/src/views/SettingsView.vue`
- Modify: `frontend/src/i18n/messages/en.ts`
- Modify: `frontend/src/i18n/messages/zh.ts`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

**Step 1: Write the failing test**

```ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import SettingsView from './SettingsView.vue'
import { useUserStore } from '../stores/user'

describe('SettingsView', () => {
  it('toggles locale via store', async () => {
    setActivePinia(createPinia())
    const i18n = createI18n({
      legacy: false,
      globalInjection: true,
      locale: 'en',
      messages: {
        en: { settings: { title: 'Settings', language: 'Language', zh: '中文', en: 'EN' } },
        zh: { settings: { title: '设置', language: '语言', zh: '中文', en: 'EN' } }
      }
    })

    const wrapper = mount(SettingsView, {
      global: { plugins: [i18n] }
    })

    const store = useUserStore()
    expect(store.locale).toBeDefined()

    await wrapper.find('[data-locale=\"zh\"]').trigger('click')
    expect(store.locale).toBe('zh')
  })
})
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/views/SettingsView.test.ts`  
Expected: FAIL with "Cannot find module './SettingsView.vue'" or missing component.

**Step 3: Write minimal implementation**

```vue
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
              @click="setLocale('zh')"
            >
              {{ $t('settings.zh') }}
            </button>
            <button
              class="toggle-btn"
              :class="{ active: locale === 'en' }"
              data-locale="en"
              @click="setLocale('en')"
            >
              {{ $t('settings.en') }}
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
const { locale } = storeToRefs(userStore)

function setLocale(next: 'en' | 'zh') {
  userStore.setLocale(next)
}
</script>
```

Add `settings.*` keys to `en.ts` and `zh.ts`.  
Upgrade `vue-i18n` to `^11.x` in `package.json`.

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/views/SettingsView.test.ts`  
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/views/SettingsView.vue frontend/src/views/SettingsView.test.ts frontend/src/i18n/messages/en.ts frontend/src/i18n/messages/zh.ts frontend/package.json frontend/package-lock.json
git commit -m "feat: add settings view and i18n v11"
```

---

### Task 2: Route + move locale toggle into Settings (TDD)

**Files:**
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/router/index.test.ts`
- Modify: `frontend/src/components/TopNav.vue`
- Modify: `frontend/src/views/DashboardView.vue`

**Step 1: Write the failing test**

```ts
import { describe, it, expect } from 'vitest'
import router from './index'

describe('router', () => {
  it('contains settings route', () => {
    const hasSettings = router.getRoutes().some((r) => r.path === '/settings')
    expect(hasSettings).toBe(true)
  })
})
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/router/index.test.ts`  
Expected: FAIL (route missing).

**Step 3: Write minimal implementation**

```ts
import SettingsView from '../views/SettingsView.vue'

// routes:
{ path: '/settings', name: 'settings', component: SettingsView }
```

Update Dashboard "Settings" button to a `RouterLink` pointing to `/settings`.  
Remove the language toggle button from `TopNav.vue`.

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/router/index.test.ts`  
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/router/index.ts frontend/src/router/index.test.ts frontend/src/components/TopNav.vue frontend/src/views/DashboardView.vue
git commit -m "feat: add settings route and move locale toggle"
```
