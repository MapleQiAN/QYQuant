// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import ResetPasswordView from './ResetPasswordView.vue'

const { replaceMock, resetPasswordMock } = vi.hoisted(() => ({
  replaceMock: vi.fn(),
  resetPasswordMock: vi.fn(),
}))

const { toastSuccessMock, toastErrorMock } = vi.hoisted(() => ({
  toastSuccessMock: vi.fn(),
  toastErrorMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    query: { token: 'token-123' },
  }),
  useRouter: () => ({
    replace: replaceMock,
  }),
}))

vi.mock('../api/auth', () => ({
  resetPassword: resetPasswordMock,
}))

vi.mock('../lib/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: toastErrorMock,
  }
}))

describe('ResetPasswordView', () => {
  beforeEach(() => {
    replaceMock.mockReset()
    resetPasswordMock.mockReset()
    toastSuccessMock.mockReset()
    toastErrorMock.mockReset()
  })

  function mountView() {
    return mount(ResetPasswordView, {
      global: {
        plugins: [
          createI18n({
            legacy: false,
            locale: 'en',
            messages: {
              en: {
                auth: {
                  passwordTooShort: 'Password too short',
                },
                resetPassword: {
                  title: 'Reset Password',
                  passwordPlaceholder: 'New password',
                  submitButton: 'Reset',
                  submitting: 'Resetting',
                  tokenMissing: 'Token missing',
                  resetFailed: 'Reset failed',
                }
              }
            }
          })
        ]
      }
    })
  }

  it('submits token and new password', async () => {
    resetPasswordMock.mockResolvedValueOnce({ message: 'reset ok' })

    const wrapper = mountView()
    await wrapper.get('[data-test="reset-password"]').setValue('NewSecret123!')
    await wrapper.get('[data-test="reset-submit"]').trigger('click')
    await flushPromises()

    expect(resetPasswordMock).toHaveBeenCalledWith('token-123', 'NewSecret123!')
    expect(replaceMock).toHaveBeenCalledWith('/login')
    expect(toastSuccessMock).toHaveBeenCalledWith('reset ok')
  })
})
