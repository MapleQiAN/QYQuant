// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import LoginView from './LoginView.vue'

const { replaceMock, refreshProfileMock, sendCodeMock, loginMock } = vi.hoisted(() => ({
  replaceMock: vi.fn(),
  refreshProfileMock: vi.fn(),
  sendCodeMock: vi.fn(),
  loginMock: vi.fn(),
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
}))

describe('LoginView', () => {
  beforeEach(() => {
    replaceMock.mockReset()
    refreshProfileMock.mockReset()
    sendCodeMock.mockReset()
    loginMock.mockReset()
    localStorage.clear()
  })

  it('sends verification code with email payload', async () => {
    sendCodeMock.mockResolvedValueOnce({ message: 'ok' })

    const wrapper = mount(LoginView)

    await wrapper.get('[data-test="mode-email"]').trigger('click')
    await wrapper.get('[data-test="email-input"]').setValue('alice@example.com')
    await wrapper.get('[data-test="send-code"]').trigger('click')
    await flushPromises()

    expect(sendCodeMock).toHaveBeenCalledWith({ email: 'alice@example.com' })
    expect(wrapper.text()).toContain('验证码已发送至 alice@example.com')
  })

  it('submits email login and redirects after profile refresh', async () => {
    sendCodeMock.mockResolvedValueOnce({ message: 'ok' })
    loginMock.mockResolvedValueOnce({
      access_token: 'token-1',
      data: {
        user_id: 'user-1',
        email: 'al***@example.com',
        nickname: 'Alice',
        plan_level: 'free',
      },
    })
    refreshProfileMock.mockResolvedValueOnce(undefined)
    replaceMock.mockResolvedValueOnce(undefined)

    const wrapper = mount(LoginView)

    await wrapper.get('[data-test="mode-email"]').trigger('click')
    await wrapper.get('[data-test="email-input"]').setValue('alice@example.com')
    await wrapper.get('[data-test="send-code"]').trigger('click')
    await flushPromises()

    await wrapper.get('[data-test="code-input"]').setValue('123456')
    await wrapper.get('[data-test="submit-login"]').trigger('click')
    await flushPromises()

    expect(loginMock).toHaveBeenCalledWith({
      email: 'alice@example.com',
      code: '123456',
    })
    expect(localStorage.getItem('qyquant-token')).toBe('token-1')
    expect(refreshProfileMock).toHaveBeenCalled()
    expect(replaceMock).toHaveBeenCalledWith('/')
  })

  it('shows nickname step when backend requires registration completion', async () => {
    sendCodeMock.mockResolvedValueOnce({ message: 'ok' })
    loginMock.mockRejectedValueOnce({ code: 'NICKNAME_REQUIRED' })

    const wrapper = mount(LoginView)

    await wrapper.get('[data-test="mode-email"]').trigger('click')
    await wrapper.get('[data-test="email-input"]').setValue('alice@example.com')
    await wrapper.get('[data-test="send-code"]').trigger('click')
    await flushPromises()

    await wrapper.get('[data-test="code-input"]').setValue('123456')
    await wrapper.get('[data-test="submit-login"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-test="nickname-input"]').exists()).toBe(true)
  })
})
