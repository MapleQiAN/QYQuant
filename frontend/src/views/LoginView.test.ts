// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import LoginView from './LoginView.vue'

const {
  replaceMock,
  refreshProfileMock,
  loginWithPasswordMock,
  registerWithPasswordMock,
} = vi.hoisted(() => ({
  replaceMock: vi.fn(),
  refreshProfileMock: vi.fn(),
  loginWithPasswordMock: vi.fn(),
  registerWithPasswordMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  RouterLink: {
    props: ['to'],
    template: '<a :href="typeof to === \'string\' ? to : to.path"><slot /></a>',
  },
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
  loginWithPassword: loginWithPasswordMock,
  registerWithPassword: registerWithPasswordMock,
}))

describe('LoginView', () => {
  beforeEach(() => {
    replaceMock.mockReset()
    refreshProfileMock.mockReset()
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

    await wrapper.get('[data-test="email-input"]').setValue('alice@example.com')
    await wrapper.get('[data-test="password-input"]').setValue('Secret123!')
    await wrapper.get('[data-test="submit-auth"]').trigger('click')
    await flushPromises()

    expect(loginWithPasswordMock).toHaveBeenCalledWith({
      email: 'alice@example.com',
      password: 'Secret123!',
    })
    expect(localStorage.getItem('qyquant-token')).toBe('token-1')
    expect(refreshProfileMock).toHaveBeenCalled()
    expect(replaceMock).toHaveBeenCalledWith('/')
  })

  it('submits email registration with nickname', async () => {
    registerWithPasswordMock.mockResolvedValueOnce({
      access_token: 'token-2',
      data: {
        user_id: 'user-2',
        email: 'pa***@example.com',
        nickname: 'Alice',
        plan_level: 'free',
      },
    })

    const wrapper = mount(LoginView)

    await wrapper.get('[data-test="register-tab"]').trigger('click')
    await wrapper.get('[data-test="email-input"]').setValue('alice@example.com')
    await wrapper.get('[data-test="password-input"]').setValue('Secret123!')
    await wrapper.get('[data-test="nickname-input"]').setValue('Alice')
    await wrapper.get('[data-test="submit-auth"]').trigger('click')
    await flushPromises()

    expect(registerWithPasswordMock).toHaveBeenCalledWith({
      email: 'alice@example.com',
      password: 'Secret123!',
      nickname: 'Alice',
    })
  })

  it('shows forgot password link on login tab', () => {
    const wrapper = mount(LoginView)

    expect(wrapper.get('[data-test="forgot-link"]').attributes('href')).toBe('/forgot-password')
  })
})
