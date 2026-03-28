// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import LoginView from './LoginView.vue'

const {
  replaceMock,
  refreshProfileMock,
  sendCodeMock,
  loginMock,
  loginWithPasswordMock,
  registerWithPasswordMock,
} = vi.hoisted(() => ({
  replaceMock: vi.fn(),
  refreshProfileMock: vi.fn(),
  sendCodeMock: vi.fn(),
  loginMock: vi.fn(),
  loginWithPasswordMock: vi.fn(),
  registerWithPasswordMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    replace: replaceMock,
  }),
}))

vi.mock('../stores/user', () => ({
  useUserStore: () => ({
    refreshProfile: refreshProfileMock,
  }),
}))

vi.mock('../api/auth', () => ({
  sendCode: sendCodeMock,
  login: loginMock,
  loginWithPassword: loginWithPasswordMock,
  registerWithPassword: registerWithPasswordMock,
}))

describe('LoginView', () => {
  beforeEach(() => {
    replaceMock.mockReset()
    refreshProfileMock.mockReset()
    sendCodeMock.mockReset()
    loginMock.mockReset()
    loginWithPasswordMock.mockReset()
    registerWithPasswordMock.mockReset()
    localStorage.clear()
  })

  it('submits email password login and redirects after profile refresh', async () => {
    loginWithPasswordMock.mockResolvedValueOnce({
      access_token: 'token-1',
      data: {
        user_id: 'user-1',
        email: 'pa***@example.com',
        nickname: 'Alice',
        plan_level: 'free',
      },
    })
    refreshProfileMock.mockResolvedValueOnce(undefined)
    replaceMock.mockResolvedValueOnce(undefined)

    const wrapper = mount(LoginView)

    await wrapper.get('[data-test="mode-email"]').trigger('click')
    await wrapper.get('[data-test="email-input"]').setValue('alice@example.com')
    await wrapper.get('[data-test="password-input"]').setValue('Secret123!')
    await wrapper.get('[data-test="submit-email"]').trigger('click')
    await flushPromises()

    expect(loginWithPasswordMock).toHaveBeenCalledWith({
      email: 'alice@example.com',
      password: 'Secret123!',
    })
    expect(localStorage.getItem('qyquant-token')).toBe('token-1')
    expect(refreshProfileMock).toHaveBeenCalled()
    expect(replaceMock).toHaveBeenCalledWith('/')
  })

  it('submits email password registration with nickname', async () => {
    registerWithPasswordMock.mockResolvedValueOnce({
      access_token: 'token-2',
      data: {
        user_id: 'user-2',
        email: 'pa***@example.com',
        nickname: 'Alice',
        plan_level: 'free',
      },
    })
    refreshProfileMock.mockResolvedValueOnce(undefined)
    replaceMock.mockResolvedValueOnce(undefined)

    const wrapper = mount(LoginView)

    await wrapper.get('[data-test="mode-email"]').trigger('click')
    await wrapper.get('[data-test="email-register-tab"]').trigger('click')
    await wrapper.get('[data-test="email-input"]').setValue('alice@example.com')
    await wrapper.get('[data-test="password-input"]').setValue('Secret123!')
    await wrapper.get('[data-test="email-nickname-input"]').setValue('Alice')
    await wrapper.get('[data-test="submit-email"]').trigger('click')
    await flushPromises()

    expect(registerWithPasswordMock).toHaveBeenCalledWith({
      email: 'alice@example.com',
      password: 'Secret123!',
      nickname: 'Alice',
    })
    expect(localStorage.getItem('qyquant-token')).toBe('token-2')
  })

  it('still supports phone verification login flow', async () => {
    sendCodeMock.mockResolvedValueOnce({ message: 'ok' })
    loginMock.mockResolvedValueOnce({
      access_token: 'token-3',
      data: {
        user_id: 'user-3',
        phone: '138****8000',
        nickname: 'PhoneUser',
        plan_level: 'free',
      },
    })
    refreshProfileMock.mockResolvedValueOnce(undefined)
    replaceMock.mockResolvedValueOnce(undefined)

    const wrapper = mount(LoginView)

    await wrapper.get('[data-test="phone-input"]').setValue('13800138000')
    await wrapper.get('[data-test="send-code"]').trigger('click')
    await flushPromises()
    await wrapper.get('[data-test="code-input"]').setValue('123456')
    await wrapper.get('[data-test="submit-login"]').trigger('click')
    await flushPromises()

    expect(sendCodeMock).toHaveBeenCalledWith({ phone: '13800138000' })
    expect(loginMock).toHaveBeenCalledWith({
      phone: '13800138000',
      code: '123456',
    })
  })
})
