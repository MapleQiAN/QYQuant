<template>
  <section class="profile-view">
    <div class="profile-layout">
      <aside class="profile-sidebar">
        <div class="hero-card card">
          <div class="hero-avatar-area">
            <img v-if="form.avatar_url" :src="form.avatar_url" alt="avatar" class="hero-avatar" />
            <div v-else class="hero-avatar hero-avatar-fallback">{{ avatarInitial }}</div>
          </div>
          <h2 class="hero-nickname">{{ userStore.profile.nickname || '—' }}</h2>
          <span :class="['hero-plan-badge', `hero-plan-badge--${planLevel}`]">{{ planDisplayName }}</span>
          <p class="hero-bio">{{ userStore.profile.bio || $t('profile.noBio') }}</p>
        </div>
      </aside>

      <div class="profile-main">
        <div class="card">
          <div class="tab-row">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              :class="['tab-btn', { active: activeTab === tab.key }]"
              type="button"
              @click="activeTab = tab.key"
            >
              {{ $t(tab.label) }}
            </button>
          </div>

          <!-- Basic Info -->
          <div v-if="activeTab === 'basic'" class="tab-content">
            <div class="section-header">
              <h3>{{ $t('profile.basicTitle') }}</h3>
              <div class="section-actions">
                <template v-if="editingBasic">
                  <button class="btn-ghost" type="button" @click="cancelBasic">{{ $t('common.cancel') }}</button>
                  <button class="primary-btn" type="button" :disabled="saving" @click="submitProfile">{{ $t('common.save') }}</button>
                </template>
                <button v-else class="btn-ghost" type="button" @click="startEditBasic">{{ $t('common.edit') }}</button>
              </div>
            </div>

            <form class="field-grid" @submit.prevent="submitProfile">
              <label class="field">
                <span>{{ $t('settings.avatarLabel') }}</span>
                <div v-if="editingBasic" class="avatar-upload-row">
                  <img v-if="avatarPreview" :src="avatarPreview" alt="preview" class="avatar-sm" />
                  <div v-else class="avatar-sm avatar-sm-fallback">{{ avatarInitial }}</div>
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp,image/gif"
                    @change="handleAvatarChange"
                  />
                </div>
                <span v-else class="field-value">
                  <img v-if="form.avatar_url" :src="form.avatar_url" alt="avatar" class="avatar-sm" />
                  <span v-else class="field-value-empty">—</span>
                </span>
              </label>

              <label class="field">
                <span>{{ $t('settings.nicknameLabel') }}</span>
                <input v-if="editingBasic" v-model="form.nickname" type="text" maxlength="30" />
                <span v-else class="field-value">{{ userStore.profile.nickname || '—' }}</span>
              </label>

              <label class="field">
                <span>{{ $t('settings.bioLabel') }}</span>
                <textarea v-if="editingBasic" v-model="form.bio" rows="3" maxlength="200"></textarea>
                <span v-else class="field-value">{{ userStore.profile.bio || '—' }}</span>
              </label>

              <label class="field">
                <span>{{ $t('profile.location') }}</span>
                <input v-if="editingBasic" v-model="form.location" type="text" maxlength="100" />
                <span v-else class="field-value">{{ userStore.profile.location || '—' }}</span>
              </label>

              <label class="field">
                <span>{{ $t('profile.website') }}</span>
                <input v-if="editingBasic" v-model="form.website_url" type="text" maxlength="500" />
                <span v-else class="field-value">
                  <a v-if="userStore.profile.website_url" :href="userStore.profile.website_url" target="_blank" rel="noopener">{{ userStore.profile.website_url }}</a>
                  <span v-else>—</span>
                </span>
              </label>
            </form>
          </div>

          <!-- Trading Profile -->
          <div v-if="activeTab === 'trading'" class="tab-content">
            <div class="section-header">
              <h3>{{ $t('profile.tradingTitle') }}</h3>
              <div class="section-actions">
                <template v-if="editingTrading">
                  <button class="btn-ghost" type="button" @click="cancelTrading">{{ $t('common.cancel') }}</button>
                  <button class="primary-btn" type="button" :disabled="saving" @click="submitProfile">{{ $t('common.save') }}</button>
                </template>
                <button v-else class="btn-ghost" type="button" @click="startEditTrading">{{ $t('common.edit') }}</button>
              </div>
            </div>

            <form class="field-grid" @submit.prevent="submitProfile">
              <label class="field">
                <span>{{ $t('profile.tradingExperience') }}</span>
                <select v-if="editingTrading" v-model="form.trading_experience">
                  <option value="">{{ $t('profile.notSet') }}</option>
                  <option value="beginner">{{ $t('profile.experienceBeginner') }}</option>
                  <option value="intermediate">{{ $t('profile.experienceIntermediate') }}</option>
                  <option value="advanced">{{ $t('profile.experienceAdvanced') }}</option>
                  <option value="professional">{{ $t('profile.experienceProfessional') }}</option>
                </select>
                <span v-else class="field-value">{{ experienceLabel }}</span>
              </label>

              <div class="field">
                <span>{{ $t('profile.preferredMarkets') }}</span>
                <div v-if="editingTrading" class="market-chips">
                  <button
                    v-for="m in marketOptions"
                    :key="m.key"
                    :class="['chip', { active: selectedMarkets.includes(m.key) }]"
                    type="button"
                    @click="toggleMarket(m.key)"
                  >
                    {{ m.label }}
                  </button>
                </div>
                <span v-else class="field-value">{{ marketsLabel }}</span>
              </div>
            </form>
          </div>

          <!-- Account -->
          <div v-if="activeTab === 'account'" class="tab-content">
            <div class="section-header">
              <h3>{{ $t('profile.accountTitle') }}</h3>
            </div>
            <dl class="field-list">
              <dt>{{ $t('profile.email') }}</dt>
              <dd>{{ userStore.profile.email || '—' }}</dd>
              <dt>{{ $t('profile.phone') }}</dt>
              <dd>{{ userStore.profile.phone || '—' }}</dd>
              <dt>{{ $t('profile.userId') }}</dt>
              <dd>{{ userStore.profile.id || '—' }}</dd>
              <dt>{{ $t('profile.planLevel') }}</dt>
              <dd>{{ planDisplayName }}</dd>
              <dt>{{ $t('profile.joinDate') }}</dt>
              <dd>{{ userStore.profile.created_at || '—' }}</dd>
            </dl>
          </div>

          <!-- Preferences -->
          <div v-if="activeTab === 'preferences'" class="tab-content">
            <div class="section-header">
              <h3>{{ $t('profile.preferencesTitle') }}</h3>
            </div>

            <div class="pref-row">
              <div>
                <h4>{{ $t('settings.language') }}</h4>
                <p class="hint">{{ $t('settings.languageHint') }}</p>
              </div>
              <div class="toggle">
                <button :class="['toggle-btn', { active: locale === 'zh' }]" type="button" @click="setLocale('zh')">{{ $t('settings.zh') }}</button>
                <button :class="['toggle-btn', { active: locale === 'en' }]" type="button" @click="setLocale('en')">{{ $t('settings.en') }}</button>
              </div>
            </div>

            <div class="pref-row">
              <div>
                <h4>{{ $t('settings.marketStyle') }}</h4>
                <p class="hint">{{ $t('settings.marketStyleHint') }}</p>
              </div>
              <div class="toggle">
                <button :class="['toggle-btn', { active: marketStyle === 'cn' }]" type="button" @click="setMarketStyle('cn')">{{ $t('settings.marketStyleCn') }}</button>
                <button :class="['toggle-btn', { active: marketStyle === 'us' }]" type="button" @click="setMarketStyle('us')">{{ $t('settings.marketStyleUs') }}</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { uploadPublicImage } from '../api/files'
import { updateMyProfile } from '../api/users'
import { toast } from '../lib/toast'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const { locale, marketStyle } = storeToRefs(userStore)

type TabKey = 'basic' | 'trading' | 'account' | 'preferences'

const tabs: { key: TabKey; label: string }[] = [
  { key: 'basic', label: 'profile.tabBasic' },
  { key: 'trading', label: 'profile.tabTrading' },
  { key: 'account', label: 'profile.tabAccount' },
  { key: 'preferences', label: 'profile.tabPreferences' },
]

const activeTab = ref<TabKey>('basic')
const editingBasic = ref(false)
const editingTrading = ref(false)
const saving = ref(false)
const selectedAvatarFile = ref<File | null>(null)
const avatarPreview = ref('')

const form = reactive({
  nickname: '',
  bio: '',
  avatar_url: '',
  location: '',
  website_url: '',
  trading_experience: '',
  preferred_markets: '',
})

const selectedMarkets = ref<string[]>([])

const marketOptions = [
  { key: 'a_share', label: 'A 股' },
  { key: 'crypto', label: 'Crypto' },
  { key: 'us_stock', label: 'US Stock' },
  { key: 'forex', label: 'Forex' },
  { key: 'futures', label: 'Futures' },
]

const avatarInitial = computed(() => userStore.profile.nickname?.slice(0, 1)?.toUpperCase() || 'Q')
const planLevel = computed(() => userStore.profile.plan_level || 'free')
const planDisplayName = computed(() => {
  const names: Record<string, string> = { free: 'Free', go: 'Go', plus: 'Plus', pro: 'Pro', ultra: 'Ultra' }
  return names[planLevel.value] || 'Free'
})

const experienceLabel = computed(() => {
  const map: Record<string, string> = {
    beginner: 'Beginner',
    intermediate: 'Intermediate',
    advanced: 'Advanced',
    professional: 'Professional',
  }
  return map[userStore.profile.trading_experience || ''] || '—'
})

const marketsLabel = computed(() => {
  const raw = userStore.profile.preferred_markets
  if (!raw) return '—'
  return raw
})

function syncForm() {
  form.nickname = userStore.profile.nickname || ''
  form.bio = userStore.profile.bio || ''
  form.avatar_url = userStore.profile.avatar_url || ''
  form.location = userStore.profile.location || ''
  form.website_url = userStore.profile.website_url || ''
  form.trading_experience = userStore.profile.trading_experience || ''
  form.preferred_markets = userStore.profile.preferred_markets || ''
  selectedMarkets.value = form.preferred_markets ? form.preferred_markets.split(',').filter(Boolean) : []
  avatarPreview.value = userStore.profile.avatar_url || ''
}

function startEditBasic() {
  syncForm()
  editingBasic.value = true
}

function startEditTrading() {
  syncForm()
  editingTrading.value = true
}

function cancelBasic() {
  editingBasic.value = false
  syncForm()
}

function cancelTrading() {
  editingTrading.value = false
  syncForm()
}

function toggleMarket(key: string) {
  const idx = selectedMarkets.value.indexOf(key)
  if (idx >= 0) {
    selectedMarkets.value = [...selectedMarkets.value.slice(0, idx), ...selectedMarkets.value.slice(idx + 1)]
  } else {
    selectedMarkets.value = [...selectedMarkets.value, key]
  }
}

function handleAvatarChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] || null
  selectedAvatarFile.value = file
  if (file && typeof URL !== 'undefined' && typeof URL.createObjectURL === 'function') {
    avatarPreview.value = URL.createObjectURL(file)
  }
}

function setLocale(next: 'en' | 'zh') {
  userStore.setLocale(next)
}

function setMarketStyle(next: 'cn' | 'us') {
  userStore.setMarketStyle(next)
}

async function submitProfile() {
  if (saving.value) return
  saving.value = true
  try {
    let avatarUrl = userStore.profile.avatar_url || ''
    if (selectedAvatarFile.value) {
      const uploaded = await uploadPublicImage(selectedAvatarFile.value)
      avatarUrl = uploaded.url
    }

    const payload: Record<string, string> = {
      nickname: form.nickname.trim(),
      bio: form.bio.trim(),
      avatar_url: avatarUrl,
      location: form.location.trim(),
      website_url: form.website_url.trim(),
      trading_experience: form.trading_experience,
      preferred_markets: selectedMarkets.value.join(','),
    }

    const profile = await updateMyProfile(payload)
    userStore.applyRemoteProfile(profile)
    selectedAvatarFile.value = null
    editingBasic.value = false
    editingTrading.value = false
    syncForm()
    toast.success('Profile saved')
  } catch (error: any) {
    toast.error(error?.message || 'Save failed')
  } finally {
    saving.value = false
  }
}

watch(
  () => [userStore.profileLoaded, userStore.profile.id],
  () => syncForm(),
  { immediate: true }
)

onMounted(async () => {
  if (userStore.token && !userStore.profileLoaded && !userStore.profileLoading) {
    await userStore.loadProfile()
  }
})
</script>

<style scoped>
.profile-view {
  width: 100%;
}

.profile-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: var(--spacing-xl);
  align-items: start;
}

/* Sidebar hero card */
.hero-card {
  display: grid;
  gap: var(--spacing-md);
  padding: var(--spacing-xl) var(--spacing-lg);
  text-align: center;
}

.hero-avatar {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--color-border);
  margin: 0 auto;
}

.hero-avatar-fallback {
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #0f766e, #0ea5e9);
  color: #fff;
  font-size: 36px;
  font-weight: 700;
}

.hero-nickname {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
}

.hero-plan-badge {
  display: inline-block;
  padding: 2px 12px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.04em;
}

.hero-plan-badge--free { background: rgba(0, 0, 0, 0.06); color: var(--color-text-muted); }
.hero-plan-badge--go { background: #ecfdf5; color: #059669; }
.hero-plan-badge--plus { background: var(--color-primary-bg); color: var(--color-primary); }
.hero-plan-badge--pro { background: #f5f3ff; color: #7c3aed; }
.hero-plan-badge--ultra { background: #fffbeb; color: #92400e; }

.hero-bio {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* Tabs */
.card {
  padding: var(--spacing-lg);
}

.tab-row {
  display: flex;
  gap: var(--spacing-xs);
  border-bottom: 2px solid var(--color-border-light);
  margin-bottom: var(--spacing-lg);
}

.tab-btn {
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  padding: var(--spacing-sm) var(--spacing-md);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--color-text-primary);
}

.tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

/* Sections */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.section-header h3 {
  margin: 0;
  font-size: var(--font-size-md);
}

.section-actions {
  display: flex;
  gap: var(--spacing-sm);
}

/* Form */
.field-grid {
  display: grid;
  gap: var(--spacing-md);
}

.field {
  display: grid;
  gap: var(--spacing-xs);
}

.field > span:first-child {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
}

.field input,
.field select,
.field textarea {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-sm) var(--spacing-md);
  font: inherit;
  background: var(--color-surface);
  color: var(--color-text-primary);
}

.field textarea {
  resize: vertical;
}

.field-value {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.field-value-empty {
  color: var(--color-text-muted);
}

.avatar-sm {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-sm-fallback {
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #0f766e, #0ea5e9);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
}

.avatar-upload-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

/* Market chips */
.market-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.chip {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: var(--spacing-xs) var(--spacing-md);
  font: inherit;
  font-size: var(--font-size-sm);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.chip:hover {
  border-color: var(--color-primary);
}

.chip.active {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-color: var(--color-primary);
}

/* Account list */
.field-list {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--spacing-sm) var(--spacing-lg);
  margin: 0;
}

.field-list dt {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
}

.field-list dd {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

/* Preferences */
.pref-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-xl);
  padding: var(--spacing-md) 0;
}

.pref-row + .pref-row {
  border-top: 1px solid var(--color-border-light);
}

.pref-row h4 {
  margin: 0;
  font-size: var(--font-size-sm);
}

.hint {
  margin: var(--spacing-xs) 0 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

/* Toggle */
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

/* Buttons */
.primary-btn {
  border: none;
  border-radius: var(--radius-full);
  padding: var(--spacing-xs) var(--spacing-md);
  font: inherit;
  cursor: pointer;
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.btn-ghost {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  padding: var(--spacing-xs) var(--spacing-md);
  font: inherit;
  cursor: pointer;
  background: transparent;
  color: var(--color-text-secondary);
}

.btn-ghost:hover {
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

/* Responsive */
@media (max-width: 768px) {
  .profile-layout {
    grid-template-columns: 1fr;
  }
}
</style>
