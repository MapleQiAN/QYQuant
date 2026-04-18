import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import SettingsView from './SettingsView.vue'
import { useUserStore } from '../stores/user'

vi.mock('vue-router', () => ({
  useRoute: () => ({
    query: {},
  }),
}))

const {
  updateMyProfileMock,
  fetchIntegrationProvidersMock,
  fetchIntegrationsMock,
  createIntegrationMock,
  validateIntegrationMock,
  fetchIntegrationAccountMock,
  toastSuccessMock,
  toastErrorMock,
  uploadPublicImageMock,
  fetchIntegrationPositionsMock,
} = vi.hoisted(() => ({
  updateMyProfileMock: vi.fn(),
  fetchIntegrationProvidersMock: vi.fn(),
  fetchIntegrationsMock: vi.fn(),
  createIntegrationMock: vi.fn(),
  validateIntegrationMock: vi.fn(),
  fetchIntegrationAccountMock: vi.fn(),
  toastSuccessMock: vi.fn(),
  toastErrorMock: vi.fn(),
  uploadPublicImageMock: vi.fn(),
  fetchIntegrationPositionsMock: vi.fn(),
}))

vi.mock('../api/users', async () => {
  const actual = await vi.importActual<typeof import('../api/users')>('../api/users')
  return {
    ...actual,
    updateMyProfile: updateMyProfileMock,
  }
})

vi.mock('../api/files', () => ({
  uploadPublicImage: uploadPublicImageMock,
}))

vi.mock('../lib/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: toastErrorMock,
  }
}))

vi.mock('../api/integrations', () => ({
  fetchIntegrationProviders: fetchIntegrationProvidersMock,
  fetchIntegrations: fetchIntegrationsMock,
  createIntegration: createIntegrationMock,
  validateIntegration: validateIntegrationMock,
  fetchIntegrationAccount: fetchIntegrationAccountMock,
  fetchIntegrationPositions: fetchIntegrationPositionsMock,
}))

function buildI18n() {
  return createI18n({
    legacy: false,
    globalInjection: true,
    locale: 'en',
    messages: {
      en: {
        settings: {
          title: 'Settings',
          profileTitle: 'Profile',
          profileHint: 'Update how you appear in the community square.',
          nicknameLabel: 'Nickname',
          bioLabel: 'Bio',
          avatarLabel: 'Avatar',
          avatarAction: 'Upload avatar',
          saveProfileAction: 'Save profile',
          language: 'Language',
          languageHint: 'Choose your interface language.',
          zh: 'ZH',
          en: 'EN',
          marketStyle: 'Market Color Style',
          marketStyleHint: 'Choose how price moves are colored.',
          marketStyleCn: 'A-share style',
          marketStyleUs: 'US style',
          integrationsTitle: 'Integrations',
          integrationsHint: 'Connect broker APIs and market data providers.',
          providerLabel: 'Provider',
          displayNameLabel: 'Display name',
          connectAction: 'Connect',
          validateAction: 'Validate',
          loadAccountAction: 'Load account',
          loadPositionsAction: 'Load positions',
          emptyIntegrations: 'No integrations yet.'
        }
      },
      zh: {
        settings: {
          title: '设置',
          profileTitle: '个人资料',
          profileHint: '更新你在广场中的展示信息。',
          nicknameLabel: '昵称',
          bioLabel: '简介',
          avatarLabel: '头像',
          avatarAction: '上传头像',
          saveProfileAction: '保存资料',
          language: '语言',
          languageHint: '选择界面语言。',
          zh: '中文',
          en: 'EN',
          marketStyle: '行情配色',
          marketStyleHint: '选择涨跌颜色风格。',
          marketStyleCn: 'A股风格',
          marketStyleUs: '美股风格',
          integrationsTitle: '数据源与券商连接',
          integrationsHint: '连接你的券商 API 和市场数据源。',
          providerLabel: 'Provider',
          displayNameLabel: 'Display name',
          connectAction: 'Connect',
          validateAction: 'Validate',
          loadAccountAction: 'Load account',
          loadPositionsAction: 'Load positions',
          emptyIntegrations: 'No integrations yet.'
        }
      }
    }
  })
}

describe('SettingsView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    updateMyProfileMock.mockReset()
    fetchIntegrationProvidersMock.mockReset()
    fetchIntegrationsMock.mockReset()
    createIntegrationMock.mockReset()
    validateIntegrationMock.mockReset()
    fetchIntegrationAccountMock.mockReset()
    uploadPublicImageMock.mockReset()
    fetchIntegrationPositionsMock.mockReset()
    toastSuccessMock.mockReset()
    toastErrorMock.mockReset()

    fetchIntegrationProvidersMock.mockResolvedValue([
      {
        key: 'longport',
        name: 'LongPort',
        type: 'broker_account',
        mode: 'hosted',
        capabilities: { positions: true },
        configSchema: {
          public_fields: ['region'],
          secret_fields: ['access_token']
        },
        isEnabled: true
      }
    ])
    fetchIntegrationsMock.mockResolvedValue([
      {
        id: 'integration-1',
        providerKey: 'longport',
        displayName: 'Main Account',
        status: 'active',
        configPublic: {},
        lastValidatedAt: null,
        lastSuccessAt: null,
        lastFailureAt: null,
        lastErrorMessage: null,
        createdAt: null,
        updatedAt: null
      }
    ])
    validateIntegrationMock.mockResolvedValue({ status: 'valid', message: 'ok' })
    fetchIntegrationAccountMock.mockResolvedValue({ currency: 'HKD', equity: '12345.67' })
    fetchIntegrationPositionsMock.mockResolvedValue([{ symbol: '00700.HK', quantity: '100', market: 'hk' }])
    updateMyProfileMock.mockImplementation(async (payload: Record<string, string>) => ({
      id: 'user-1',
      nickname: payload.nickname ?? 'Quant Pro',
      avatar_url: payload.avatar_url ?? '',
      bio: payload.bio ?? '',
      role: 'user',
      plan_level: 'free',
      is_banned: false,
      onboarding_completed: true,
      sim_disclaimer_accepted: false,
    }))
    uploadPublicImageMock.mockResolvedValue({
      id: 'file-1',
      url: '/api/files/file-1/content',
    })

    const userStore = useUserStore()
    userStore.applyRemoteProfile({
      id: 'user-1',
      nickname: 'Quant Pro',
      avatar_url: '',
      bio: 'Initial bio',
      role: 'user',
      plan_level: 'free',
      is_banned: false,
      onboarding_completed: true,
      sim_disclaimer_accepted: false,
    })
  })

  it('toggles locale via store and loads integrations on mount', async () => {
    const wrapper = mount(SettingsView, {
      global: { plugins: [buildI18n()] }
    })
    await flushPromises()

    const store = useUserStore()
    expect(store.locale).toBeDefined()
    expect(fetchIntegrationProvidersMock).toHaveBeenCalledTimes(1)
    expect(fetchIntegrationsMock).toHaveBeenCalledTimes(1)

    await wrapper.find('[data-locale="zh"]').trigger('click')
    expect(store.locale).toBe('zh')
  })

  it('creates and manages integrations from settings', async () => {
    createIntegrationMock.mockResolvedValueOnce({
      id: 'integration-2',
      providerKey: 'longport',
      displayName: 'New Account',
      status: 'active',
      configPublic: {},
      lastValidatedAt: null,
      lastSuccessAt: null,
      lastFailureAt: null,
      lastErrorMessage: null,
      createdAt: null,
      updatedAt: null
    })

    const wrapper = mount(SettingsView, {
      global: { plugins: [buildI18n()] }
    })
    await flushPromises()

    await wrapper.find('[data-provider-key="longport"]').setValue('longport')
    await wrapper.find('[data-display-name="integration-display-name"]').setValue('New Account')
    await wrapper.find('[data-public-field="region"]').setValue('hk')
    await wrapper.find('[data-secret-field="access_token"]').setValue('token-1')
    await wrapper.find('[data-action="connect-integration"]').trigger('submit')

    expect(createIntegrationMock).toHaveBeenCalledWith({
      providerKey: 'longport',
      displayName: 'New Account',
      configPublic: { region: 'hk' },
      secretPayload: { access_token: 'token-1' }
    })

    await wrapper.find('[data-action="validate-integration-integration-1"]').trigger('click')
    await wrapper.find('[data-action="load-account-integration-1"]').trigger('click')
    await wrapper.find('[data-action="load-positions-integration-1"]').trigger('click')

    expect(validateIntegrationMock).toHaveBeenCalledWith('integration-1')
    expect(fetchIntegrationAccountMock).toHaveBeenCalledWith('integration-1')
    expect(fetchIntegrationPositionsMock).toHaveBeenCalledWith('integration-1')
  })

  it('uploads avatar and saves profile changes through the user store', async () => {
    const wrapper = mount(SettingsView, {
      global: { plugins: [buildI18n()] }
    })
    await flushPromises()

    await wrapper.find('[data-profile-field="nickname"]').setValue('Quant Alice')
    await wrapper.find('[data-profile-field="bio"]').setValue('Trend follower')

    const avatarFile = new File(['avatar'], 'avatar.png', { type: 'image/png' })
    const avatarInput = wrapper.get('[data-profile-field="avatar"]')
    Object.defineProperty(avatarInput.element, 'files', {
      value: [avatarFile],
      configurable: true,
    })
    await avatarInput.trigger('change')
    await flushPromises()

    await wrapper.find('[data-action="save-profile"]').trigger('submit')
    await flushPromises()

    expect(uploadPublicImageMock).toHaveBeenCalledTimes(1)
    expect(uploadPublicImageMock).toHaveBeenCalledWith(avatarFile)
    expect(updateMyProfileMock).toHaveBeenCalledWith({
      nickname: 'Quant Alice',
      bio: 'Trend follower',
      avatar_url: '/api/files/file-1/content',
    })

    const userStore = useUserStore()
    expect(userStore.profile.nickname).toBe('Quant Alice')
    expect(userStore.profile.avatar_url).toBe('/api/files/file-1/content')
    expect(userStore.profile.bio).toBe('Trend follower')
    expect(toastSuccessMock).toHaveBeenCalledTimes(1)
  })

  it('syncs form fields when remote profile arrives after mount', async () => {
    const userStore = useUserStore()
    userStore.profileLoaded = false
    userStore.profile.nickname = 'Quant Pro'
    userStore.profile.bio = ''

    const wrapper = mount(SettingsView, {
      global: { plugins: [buildI18n()] }
    })
    await flushPromises()

    userStore.applyRemoteProfile({
      id: 'user-1',
      nickname: 'Remote Alice',
      avatar_url: '/api/files/file-9/content',
      bio: 'Loaded later',
      role: 'user',
      plan_level: 'free',
      is_banned: false,
      onboarding_completed: true,
      sim_disclaimer_accepted: false,
    })
    await flushPromises()

    expect((wrapper.get('[data-profile-field="nickname"]').element as HTMLInputElement).value).toBe('Remote Alice')
    expect((wrapper.get('[data-profile-field="bio"]').element as HTMLTextAreaElement).value).toBe('Loaded later')
  })

  it('shows an error when profile save fails', async () => {
    updateMyProfileMock.mockRejectedValueOnce(new Error('save failed'))

    const wrapper = mount(SettingsView, {
      global: { plugins: [buildI18n()] }
    })
    await flushPromises()

    await wrapper.find('[data-profile-field="nickname"]').setValue('Quant Alice')
    await wrapper.find('[data-action="save-profile"]').trigger('submit')
    await flushPromises()

    expect(toastErrorMock).toHaveBeenCalledTimes(1)
    expect(toastErrorMock).toHaveBeenCalledWith('save failed')
  })
})
