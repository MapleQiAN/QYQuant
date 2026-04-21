<template>
  <section class="settings-view">
    <div class="container">
      <h1 class="view-title">{{ $t('settings.title') }}</h1>

      <div class="settings-grid">
        <div class="card setting-card preferences-card">
          <div class="setting-row">
            <div class="setting-label">
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
          <div class="setting-divider" />
          <div class="setting-row">
            <div class="setting-label">
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
              <h3>{{ $t('settings.dataSourceTitle') }}</h3>
              <p class="hint">{{ $t('settings.dataSourceHint') }}</p>
            </div>
          </div>
        <form class="integration-form" data-action="connect-datasource" @submit.prevent="submitDsIntegration">
          <label class="field">
            <span>{{ $t('settings.providerLabel') }}</span>
            <QSelect v-model="dsSelectedProviderKey" :options="dataSourceProviderOptions" data-provider-key="datasource" />
          </label>
          <label class="field">
            <span>{{ $t('settings.displayNameLabel') }}</span>
            <input v-model="dsDisplayName" data-display-name="ds-display-name" type="text" />
          </label>
          <label v-for="fieldName in dsPublicFieldNames" :key="`ds-public-${fieldName}`" class="field">
            <span>{{ fieldName }}</span>
            <input v-model="dsConfigPublic[fieldName]" :data-public-field="fieldName" type="text" />
          </label>
          <label v-for="fieldName in dsSecretFieldNames" :key="`ds-secret-${fieldName}`" class="field">
            <span>{{ fieldName }}</span>
            <input v-model="dsSecretPayload[fieldName]" :data-secret-field="fieldName" type="text" />
          </label>
          <button class="primary-btn" type="submit">
            {{ $t('settings.connectAction') }}
          </button>
        </form>
        <div v-if="dataSourceIntegrations.length === 0" class="empty-state">
          {{ $t('settings.emptyDataSources') }}
        </div>
        <div v-else class="integration-list">
          <article v-for="integration in dataSourceIntegrations" :key="integration.id" class="integration-item">
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

      <div class="card setting-card integrations-card">
        <div class="setting-header integrations-header">
          <div>
            <h3>{{ $t('settings.aiSettingsTitle') }}</h3>
            <p class="hint">{{ $t('settings.aiSettingsHint') }}</p>
          </div>
        </div>
        <form class="integration-form" data-action="connect-ai" @submit.prevent="submitAiIntegration">
          <label class="field">
            <span>{{ $t('settings.providerLabel') }}</span>
            <QSelect v-model="aiSelectedProviderKey" :options="aiProviderOptions" data-provider-key="ai" />
          </label>
          <label class="field">
            <span>{{ $t('settings.displayNameLabel') }}</span>
            <input v-model="aiDisplayName" data-display-name="ai-display-name" type="text" />
          </label>
          <label v-for="fieldName in aiPublicFieldNames" :key="`ai-public-${fieldName}`" class="field">
            <span>{{ fieldName }}</span>
            <input v-model="aiConfigPublic[fieldName]" :data-public-field="fieldName" type="text" />
          </label>
          <label v-for="fieldName in aiSecretFieldNames" :key="`ai-secret-${fieldName}`" class="field">
            <span>{{ fieldName }}</span>
            <input v-model="aiSecretPayload[fieldName]" :data-secret-field="fieldName" type="text" />
          </label>
          <button class="primary-btn" type="submit">
            {{ $t('settings.addConfigAction') }}
          </button>
        </form>
        <div v-if="aiIntegrations.length === 0" class="empty-state">
          {{ $t('settings.emptyAiConnections') }}
        </div>
        <div v-else class="integration-list">
          <article
            v-for="integration in aiIntegrations"
            :key="integration.id"
            class="integration-item"
            :class="{ 'ai-active': activeAiIntegrationId === integration.id }"
          >
            <template v-if="editingAiId === integration.id">
              <div class="edit-form">
                <label class="field">
                  <span>{{ $t('settings.displayNameLabel') }}</span>
                  <input v-model="editDisplayName" type="text" />
                </label>
                <label
                  v-for="fieldName in editAiFieldNames(integration).publicFields"
                  :key="`edit-pub-${fieldName}`"
                  class="field"
                >
                  <span>{{ fieldName }}</span>
                  <input v-model="editConfigPublic[fieldName]" type="text" />
                </label>
                <label
                  v-for="fieldName in editAiFieldNames(integration).secretFields"
                  :key="`edit-sec-${fieldName}`"
                  class="field"
                >
                  <span>{{ fieldName }}</span>
                  <input v-model="editSecretPayload[fieldName]" type="text" :placeholder="$t('settings.secretPlaceholder')" />
                </label>
                <div class="edit-actions">
                  <button class="primary-btn" type="button" @click="saveEditAi(integration)">
                    {{ $t('settings.saveAction') }}
                  </button>
                  <button type="button" @click="cancelEditAi">
                    {{ $t('settings.cancelAction') }}
                  </button>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="integration-meta">
                <div class="integration-name-row">
                  <strong>{{ integration.displayName }}</strong>
                  <span v-if="activeAiIntegrationId === integration.id" class="ai-active-badge">
                    {{ $t('settings.connectedStatus') }}
                  </span>
                </div>
                <span>{{ integration.providerKey }}</span>
              </div>
              <div class="integration-actions">
                <button
                  v-if="activeAiIntegrationId !== integration.id"
                  type="button"
                  class="connect-btn"
                  :data-action="`connect-integration-${integration.id}`"
                  @click="connectAiIntegration(integration.id)"
                >
                  {{ $t('settings.connectAction') }}
                </button>
                <button
                  v-else
                  type="button"
                  class="disconnect-btn"
                  :data-action="`disconnect-integration-${integration.id}`"
                  @click="connectAiIntegration('')"
                >
                  {{ $t('settings.disconnectAction') }}
                </button>
                <button
                  type="button"
                  :data-action="`validate-integration-${integration.id}`"
                  @click="validateExistingIntegration(integration.id)"
                >
                  {{ $t('settings.validateAction') }}
                </button>
                <button
                  type="button"
                  class="edit-btn"
                  :data-action="`edit-integration-${integration.id}`"
                  @click="startEditAi(integration)"
                >
                  {{ $t('settings.editAction') }}
                </button>
                <button
                  type="button"
                  class="delete-btn"
                  :data-action="`delete-integration-${integration.id}`"
                  @click="deleteAiIntegration(integration.id)"
                >
                  {{ $t('settings.deleteAction') }}
                </button>
              </div>
              <p v-if="validationState[integration.id]" class="integration-feedback">
                {{ validationState[integration.id]?.status }} {{ validationState[integration.id]?.message || '' }}
              </p>
            </template>
          </article>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useIntegrationsStore } from '../stores/useIntegrationsStore'
import { QSelect } from '../components/ui'

const userStore = useUserStore()
const integrationsStore = useIntegrationsStore()
const route = useRoute()
const { locale, marketStyle } = storeToRefs(userStore)
const { providers, integrations, validationState, accountById, positionsById, activeAiIntegrationId } = storeToRefs(integrationsStore)

const dsSelectedProviderKey = ref('')
const dsDisplayName = ref('')
const dsConfigPublic = reactive<Record<string, string>>({})
const dsSecretPayload = reactive<Record<string, string>>({})

const aiSelectedProviderKey = ref('')
const aiDisplayName = ref('')
const aiConfigPublic = reactive<Record<string, string>>({})
const aiSecretPayload = reactive<Record<string, string>>({})

const editingAiId = ref('')
const editDisplayName = ref('')
const editConfigPublic = reactive<Record<string, string>>({})
const editSecretPayload = reactive<Record<string, string>>({})

const providerByKey = computed(() =>
  Object.fromEntries(providers.value.map((provider) => [provider.key, provider]))
)

function fieldNamesFor(providerKey: string, field: 'public_fields' | 'secret_fields' | 'fields'): string[] {
  const provider = providerByKey.value[providerKey]
  if (!provider) return []
  const schema = provider.configSchema ?? {}
  if (field === 'public_fields') {
    const fields = schema.public_fields
    return Array.isArray(fields) ? fields.map((f) => String(f)) : []
  }
  const fields = schema.secret_fields ?? schema.fields
  return Array.isArray(fields) ? fields.map((f) => String(f)) : []
}

const dsPublicFieldNames = computed(() => fieldNamesFor(dsSelectedProviderKey.value, 'public_fields'))
const dsSecretFieldNames = computed(() => fieldNamesFor(dsSelectedProviderKey.value, 'secret_fields'))

const aiPublicFieldNames = computed(() => fieldNamesFor(aiSelectedProviderKey.value, 'public_fields'))
const aiSecretFieldNames = computed(() => fieldNamesFor(aiSelectedProviderKey.value, 'secret_fields'))

const dataSourceProviders = computed(() =>
  providers.value.filter((p) => p.type === 'market_data' || p.type === 'broker_account')
)
const aiProviders = computed(() =>
  providers.value.filter((p) => p.type === 'llm')
)
const dataSourceProviderOptions = computed(() =>
  dataSourceProviders.value.map((p) => ({ label: p.name, value: p.key }))
)
const aiProviderOptions = computed(() =>
  aiProviders.value.map((p) => ({ label: p.name, value: p.key }))
)
const dataSourceIntegrations = computed(() =>
  integrations.value.filter((i) => {
    const type = providerByKey.value[i.providerKey]?.type
    return type === 'market_data' || type === 'broker_account'
  })
)
const aiIntegrations = computed(() =>
  integrations.value.filter((i) => providerByKey.value[i.providerKey]?.type === 'llm')
)

function setLocale(next: 'en' | 'zh') {
  userStore.setLocale(next)
}

function setMarketStyle(next: 'cn' | 'us') {
  userStore.setMarketStyle(next)
}

async function submitDsIntegration() {
  if (!dsSelectedProviderKey.value || !dsDisplayName.value.trim()) {
    return
  }
  const publicPayload: Record<string, string> = {}
  for (const fieldName of dsPublicFieldNames.value) {
    publicPayload[fieldName] = dsConfigPublic[fieldName] ?? ''
  }
  const secretFieldPayload: Record<string, string> = {}
  for (const fieldName of dsSecretFieldNames.value) {
    secretFieldPayload[fieldName] = dsSecretPayload[fieldName] ?? ''
  }
  await integrationsStore.createIntegration({
    providerKey: dsSelectedProviderKey.value,
    displayName: dsDisplayName.value.trim(),
    configPublic: publicPayload,
    secretPayload: secretFieldPayload
  })
}

async function submitAiIntegration() {
  if (!aiSelectedProviderKey.value || !aiDisplayName.value.trim()) {
    return
  }
  const publicPayload: Record<string, string> = {}
  for (const fieldName of aiPublicFieldNames.value) {
    publicPayload[fieldName] = aiConfigPublic[fieldName] ?? ''
  }
  const secretFieldPayload: Record<string, string> = {}
  for (const fieldName of aiSecretFieldNames.value) {
    secretFieldPayload[fieldName] = aiSecretPayload[fieldName] ?? ''
  }
  await integrationsStore.createIntegration({
    providerKey: aiSelectedProviderKey.value,
    displayName: aiDisplayName.value.trim(),
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

function connectAiIntegration(integrationId: string) {
  integrationsStore.setActiveAiIntegration(integrationId)
}

async function deleteAiIntegration(integrationId: string) {
  await integrationsStore.deleteIntegration(integrationId)
}

function editAiFieldNames(integration: { providerKey: string }) {
  return {
    publicFields: fieldNamesFor(integration.providerKey, 'public_fields'),
    secretFields: fieldNamesFor(integration.providerKey, 'secret_fields'),
  }
}

function startEditAi(integration: { id: string; providerKey: string; displayName: string; configPublic: Record<string, unknown> }) {
  editingAiId.value = integration.id
  editDisplayName.value = integration.displayName
  const fields = editAiFieldNames(integration)
  for (const key of Object.keys(editConfigPublic)) delete editConfigPublic[key]
  for (const key of Object.keys(editSecretPayload)) delete editSecretPayload[key]
  for (const f of fields.publicFields) editConfigPublic[f] = String(integration.configPublic[f] ?? '')
  for (const f of fields.secretFields) editSecretPayload[f] = ''
}

function cancelEditAi() {
  editingAiId.value = ''
}

async function saveEditAi(integration: { id: string; providerKey: string }) {
  const fields = editAiFieldNames(integration)
  const publicPayload: Record<string, string> = {}
  for (const f of fields.publicFields) publicPayload[f] = editConfigPublic[f] ?? ''
  const secretPayload: Record<string, string> = {}
  const hasSecret = fields.secretFields.some((f) => editSecretPayload[f]?.trim())
  for (const f of fields.secretFields) secretPayload[f] = editSecretPayload[f] ?? ''
  await integrationsStore.updateIntegration(integration.id, {
    displayName: editDisplayName.value.trim(),
    configPublic: publicPayload,
    ...(hasSecret ? { secretPayload } : {}),
  })
  editingAiId.value = ''
}

onMounted(async () => {
  if (userStore.token && !userStore.profileLoaded && !userStore.profileLoading) {
    await userStore.loadProfile()
  }
  await integrationsStore.loadProviders()
  await integrationsStore.loadIntegrations()
  const requestedProvider = String(route.query.provider || '').trim()
  if (requestedProvider && providers.value.some((provider) => provider.key === requestedProvider)) {
    const type = providerByKey.value[requestedProvider]?.type
    if (type === 'llm') {
      aiSelectedProviderKey.value = requestedProvider
    } else {
      dsSelectedProviderKey.value = requestedProvider
    }
    return
  }
  if (dataSourceProviders.value.length > 0) {
    dsSelectedProviderKey.value = dataSourceProviders.value[0].key
  }
  if (aiProviders.value.length > 0) {
    aiSelectedProviderKey.value = aiProviders.value[0].key
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

.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
  align-items: start;
}

.setting-card {
  padding: var(--spacing-lg);
}

.setting-card + .setting-card {
  margin-top: 0;
}

.settings-grid + .card {
  margin-top: var(--spacing-md);
}

.preferences-card {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-xl);
  padding: var(--spacing-sm) 0;
}

.setting-label h3 {
  margin: 0;
}

.setting-divider {
  height: 1px;
  background: var(--color-border-light);
  margin: var(--spacing-xs) 0;
}

.setting-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-xl);
}

.hint {
  margin: var(--spacing-xs) 0 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.integrations-card,
.integration-form {
  display: grid;
  gap: var(--spacing-md);
}

.integrations-header {
  align-items: flex-start;
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

.ai-active {
  border-color: #10b981;
  background: color-mix(in srgb, #10b981 8%, var(--color-surface));
}

.integration-name-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.ai-active-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: #10b981;
  color: #fff;
  font-size: var(--font-size-xs);
  font-weight: 600;
  line-height: 1.4;
}

.connect-btn {
  background: #10b981 !important;
  color: #fff !important;
}

.disconnect-btn {
  background: var(--color-primary-bg) !important;
  color: var(--color-text-secondary) !important;
}

.delete-btn {
  color: #ef4444 !important;
  background: color-mix(in srgb, #ef4444 10%, var(--color-surface)) !important;
}

.edit-btn {
  color: var(--color-primary) !important;
}

.edit-form {
  display: grid;
  gap: var(--spacing-sm);
}

.edit-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.edit-actions button {
  border: none;
  border-radius: var(--radius-full);
  padding: var(--spacing-xs) var(--spacing-md);
  font: inherit;
  cursor: pointer;
  background: var(--color-primary-bg);
  color: var(--color-primary);
}
</style>
