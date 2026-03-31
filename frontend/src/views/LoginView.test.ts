// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import LoginView from './LoginView.vue'

const {
  replaceMock,
  refreshProfileMock,
  loginWithPasswordMock,
  registerWithPasswordMock,
  toastSuccessMock,
} = vi.hoisted(() => ({
  replaceMock: vi.fn(),
  refreshProfileMock: vi.fn(),
  loginWithPasswordMock: vi.fn(),
  registerWithPasswordMock: vi.fn(),
  toastSuccessMock: vi.fn(),
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

vi.mock('../lib/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: vi.fn(),
  },
}))

describe('LoginView', () => {
  beforeEach(() => {
    replaceMock.mockReset()
    refreshProfileMock.mockReset()
    loginWithPasswordMock.mockReset()
    registerWithPasswordMock.mockReset()
    toastSuccessMock.mockReset()
    localStorage.clear()
  })

  function mountView() {
    return mount(LoginView, {
      global: {
        plugins: [
          createI18n({
            legacy: false,
            locale: 'en',
            messages: {
              en: {
                auth: {
                  title: 'Auth',
                  loginTab: 'Login',
                  registerTab: 'Register',
                  emailLabel: 'Email',
                  emailPlaceholder: 'Email',
                  passwordLabel: 'Password',
                  passwordPlaceholder: 'Password',
                  nicknameLabel: 'Nickname',
                  nicknamePlaceholder: 'Nickname',
                  forgotPassword: 'Forgot password',
                  loginButton: 'Login',
                  registerButton: 'Register',
                  loggingIn: 'Logging in',
                  registering: 'Registering',
                  emailRequired: 'Email required',
                  passwordRequired: 'Password required',
                  passwordTooShort: 'Password too short',
                  nicknameRequired: 'Nickname required',
                  registerFailed: 'Register failed',
                  loginFailed: 'Login failed',
                }
              }
            }
          })
        ]
      }
    })
  }

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

    const wrapper = mountView()

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
    expect(toastSuccessMock).toHaveBeenCalledWith('登录成功')
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

    const wrapper = mountView()

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
    expect(toastSuccessMock).toHaveBeenCalledWith('注册成功')
  })

  it('shows forgot password link on login tab', () => {
    const wrapper = mountView()

    expect(wrapper.get('[data-test="forgot-link"]').attributes('href')).toBe('/forgot-password')
  })
})
