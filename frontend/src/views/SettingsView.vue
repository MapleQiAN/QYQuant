<template>
  <section class="settings-view">
    <div class="container">
      <h1 class="view-title">{{ $t('settings.title') }}</h1>

      <div class="card setting-card profile-card">
        <div class="setting-header profile-header">
          <div>
            <h3>{{ $t('settings.profileTitle') }}</h3>
            <p class="hint">{{ $t('settings.profileHint') }}</p>
          </div>
        </div>

        <form class="profile-form" data-action="save-profile" @submit.prevent="submitProfile">
          <div class="profile-preview">
            <img v-if="avatarPreview" :src="avatarPreview" alt="avatar preview" class="profile-avatar" />
            <div v-else class="profile-avatar profile-avatar-fallback">
              {{ avatarFallback }}
            </div>
          </div>

          <label class="field">
            <span>{{ $t('settings.nicknameLabel') }}</span>
            <input v-model="nickname" data-profile-field="nickname" type="text" maxlength="30" @input="markProfileDirty" />
          </label>

          <label class="field">
            <span>{{ $t('settings.bioLabel') }}</span>
            <textarea v-model="bio" data-profile-field="bio" rows="4" maxlength="200" @input="markProfileDirty"></textarea>
          </label>

          <label class="field">
            <span>{{ $t('settings.avatarLabel') }}</span>
            <input
              data-profile-field="avatar"
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              @change="handleAvatarChange"
            />
          </label>

          <button class="primary-btn" type="submit" :disabled="savingProfile">
            {{ $t('settings.saveProfileAction') }}
          </button>
        </form>
      </div>

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

      <div class="card setting-card integrations-card">
        <div class="setting-header integrations-header">
          <div>
            <h3>{{ $t('settings.integrationsTitle') }}</h3>
            <p class="hint">{{ $t('settings.integrationsHint') }}</p>
          </div>
        </div>
        <form class="integration-form" data-action="connect-integration" @submit.prevent="submitIntegration">
          <label class="field">
            <span>{{ $t('settings.providerLabel') }}</span>
            <QSelect v-model="selectedProviderKey" :options="providerOptions" data-provider-key="longport" />
          </label>
          <label class="field">
            <span>{{ $t('settings.displayNameLabel') }}</span>
            <input v-model="displayName" data-display-name="integration-display-name" type="text" />
          </label>
          <label v-for="fieldName in providerPublicFieldNames" :key="`public-${fieldName}`" class="field">
            <span>{{ fieldName }}</span>
            <input v-model="configPublic[fieldName]" :data-public-field="fieldName" type="text" />
          </label>
          <label v-for="fieldName in providerSecretFieldNames" :key="`secret-${fieldName}`" class="field">
            <span>{{ fieldName }}</span>
            <input v-model="secretPayload[fieldName]" :data-secret-field="fieldName" type="text" />
          </label>
          <button class="primary-btn" type="submit">
            {{ $t('settings.connectAction') }}
          </button>
        </form>
        <div v-if="integrations.length === 0" class="empty-state">
          {{ $t('settings.emptyIntegrations') }}
        </div>
        <div v-else class="integration-list">
          <article v-for="integration in integrations" :key="integration.id" class="integration-item">
            <div class="integration-meta">
              <strong>{{ integration.displayName }}</strong>
              <span>{{ integration.providerKey }}</span>
            </div>
            <div class="integration-actions">
              <button
                type="button"
                :data-action="`validate-integration-${integration.id}`"
                @click="validateExistingIntegration(integration.id)"
              >
                {{ $t('settings.validateAction') }}
              </button>
              <button
                v-if="providerByKey[integration.providerKey]?.type === 'broker_account'"
                type="button"
                :data-action="`load-account-${integration.id}`"
                @click="loadAccount(integration.id)"
              >
                {{ $t('settings.loadAccountAction') }}
              </button>
              <button
                v-if="providerByKey[integration.providerKey]?.type === 'broker_account'"
                type="button"
                :data-action="`load-positions-${integration.id}`"
                @click="loadPositions(integration.id)"
              >
                {{ $t('settings.loadPositionsAction') }}
              </button>
            </div>
            <p v-if="validationState[integration.id]" class="integration-feedback">
              {{ validationState[integration.id]?.status }} {{ validationState[integration.id]?.message || '' }}
            </p>
            <dl v-if="accountById[integration.id]" class="integration-account">
              <template v-for="(value, key) in accountById[integration.id]" :key="key">
                <dt>{{ key }}</dt>
                <dd>{{ value }}</dd>
              </template>
            </dl>
            <ul v-if="positionsById[integration.id]?.length" class="integration-positions">
              <li v-for="position in positionsById[integration.id]" :key="JSON.stringify(position)">
                {{ position.symbol }} / {{ position.quantity }}
              </li>
            </ul>
          </article>
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
import { useIntegrationsStore } from '../stores/useIntegrationsStore'
import { QSelect } from '../components/ui'

const userStore = useUserStore()
const integrationsStore = useIntegrationsStore()
const { locale, marketStyle } = storeToRefs(userStore)
const { providers, integrations, validationState, accountById, positionsById } = storeToRefs(integrationsStore)

const nickname = ref('')
const bio = ref('')
const avatarPreview = ref('')
const selectedAvatarFile = ref<File | null>(null)
const savingProfile = ref(false)
const profileDirty = ref(false)

const selectedProviderKey = ref('')
const displayName = ref('')
const configPublic = reactive<Record<string, string>>({})
const secretPayload = reactive<Record<string, string>>({})

const selectedProvider = computed(() => providers.value.find((provider) => provider.key === selectedProviderKey.value) ?? null)
const providerByKey = computed(() =>
  Object.fromEntries(providers.value.map((provider) => [provider.key, provider]))
)
const providerPublicFieldNames = computed(() => {
  const fields = selectedProvider.value?.configSchema?.public_fields
  return Array.isArray(fields) ? fields.map((field) => String(field)) : []
})
const providerSecretFieldNames = computed(() => {
  const fields = selectedProvider.value?.configSchema?.secret_fields ?? selectedProvider.value?.configSchema?.fields
  return Array.isArray(fields) ? fields.map((field) => String(field)) : []
})
const avatarFallback = computed(() => nickname.value.trim().slice(0, 1).toUpperCase() || 'Q')

const providerOptions = computed(() =>
  providers.value.map((p) => ({ label: p.name, value: p.key }))
)

function syncProfileForm() {
  nickname.value = userStore.profile.nickname || ''
  bio.value = userStore.profile.bio || ''
  avatarPreview.value = userStore.profile.avatar_url || ''
}

function markProfileDirty() {
  profileDirty.value = true
}

function setLocale(next: 'en' | 'zh') {
  userStore.setLocale(next)
}

function setMarketStyle(next: 'cn' | 'us') {
  userStore.setMarketStyle(next)
}

function handleAvatarChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] || null
  selectedAvatarFile.value = file
  profileDirty.value = true
  const previewUrl = file && typeof URL !== 'undefined' && typeof URL.createObjectURL === 'function'
    ? URL.createObjectURL(file)
    : ''
  avatarPreview.value = previewUrl || userStore.profile.avatar_url || ''
}

async function submitProfile() {
  if (savingProfile.value) {
    return
  }

  savingProfile.value = true
  try {
    let avatarUrl = userStore.profile.avatar_url || ''
    if (selectedAvatarFile.value) {
      const uploaded = await uploadPublicImage(selectedAvatarFile.value)
      avatarUrl = uploaded.url
    }

    const profile = await updateMyProfile({
      nickname: nickname.value.trim(),
      bio: bio.value.trim(),
      avatar_url: avatarUrl,
    })
    userStore.applyRemoteProfile(profile)
    selectedAvatarFile.value = null
    profileDirty.value = false
    syncProfileForm()
    toast.success('资料已保存')
  } catch (error: any) {
    toast.error(error?.message || '保存失败')
  } finally {
    savingProfile.value = false
  }
}

async function submitIntegration() {
  if (!selectedProviderKey.value || !displayName.value.trim()) {
    return
  }
  const publicPayload: Record<string, string> = {}
  for (const fieldName of providerPublicFieldNames.value) {
    publicPayload[fieldName] = configPublic[fieldName] ?? ''
  }
  const secretFieldPayload: Record<string, string> = {}
  for (const fieldName of providerSecretFieldNames.value) {
    secretFieldPayload[fieldName] = secretPayload[fieldName] ?? ''
  }
  await integrationsStore.createIntegration({
    providerKey: selectedProviderKey.value,
    displayName: displayName.value.trim(),
    configPublic: publicPayload,
    secretPayload: secretFieldPayload
  })
}

async function validateExistingIntegration(integrationId: string) {
  await integrationsStore.validateIntegration(integrationId)
}

async function loadAccount(integrationId: string) {
  await integrationsStore.loadAccount(integrationId)
}

async function loadPositions(integrationId: string) {
  await integrationsStore.loadPositions(integrationId)
}

watch(
  () => [
    userStore.profileLoaded,
    userStore.profile.id,
    userStore.profile.nickname,
    userStore.profile.bio,
    userStore.profile.avatar_url,
  ],
  () => {
    if (!profileDirty.value) {
      syncProfileForm()
    }
  },
  { immediate: true }
)

onMounted(async () => {
  if (userStore.token && !userStore.profileLoaded && !userStore.profileLoading) {
    await userStore.loadProfile()
  }
  await integrationsStore.loadProviders()
  await integrationsStore.loadIntegrations()
  if (!selectedProviderKey.value && providers.value.length > 0) {
    selectedProviderKey.value = providers.value[0].key
  }
})
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

.profile-card,
.profile-form,
.integrations-card,
.integration-form {
  display: grid;
  gap: var(--spacing-md);
}

.profile-header,
.integrations-header {
  align-items: flex-start;
}

.profile-preview {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.profile-avatar {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--color-border);
}

.profile-avatar-fallback {
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #0f766e, #0ea5e9);
  color: #fff;
  font-size: 32px;
  font-weight: 700;
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

.field {
  display: grid;
  gap: var(--spacing-xs);
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

.primary-btn,
.integration-actions button {
  border: none;
  border-radius: var(--radius-full);
  padding: var(--spacing-xs) var(--spacing-md);
  font: inherit;
  cursor: pointer;
}

.primary-btn {
  justify-self: start;
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.integration-list {
  display: grid;
  gap: var(--spacing-sm);
}

.integration-item {
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
  display: grid;
  gap: var(--spacing-sm);
}

.integration-meta {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.integration-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.integration-actions button {
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

.integration-feedback {
  margin: 0;
  color: var(--color-text-secondary);
}

.integration-account {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, max-content));
  gap: var(--spacing-xs) var(--spacing-md);
  margin: 0;
}

.integration-account dt,
.integration-account dd {
  margin: 0;
}

.integration-positions {
  margin: 0;
  padding-left: 1rem;
}

.empty-state {
  color: var(--color-text-muted);
}
</style>
