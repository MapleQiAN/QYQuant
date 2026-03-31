// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import ForgotPasswordView from './ForgotPasswordView.vue'

const { forgotPasswordMock } = vi.hoisted(() => ({
  forgotPasswordMock: vi.fn(),
}))

vi.mock('../api/auth', () => ({
  forgotPassword: forgotPasswordMock,
}))

const { toastSuccessMock, toastErrorMock } = vi.hoisted(() => ({
  toastSuccessMock: vi.fn(),
  toastErrorMock: vi.fn(),
}))

vi.mock('../lib/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: toastErrorMock,
  }
}))

describe('ForgotPasswordView', () => {
  beforeEach(() => {
    forgotPasswordMock.mockReset()
    toastSuccessMock.mockReset()
    toastErrorMock.mockReset()
  })

  function mountView() {
    return mount(ForgotPasswordView, {
      global: {
        plugins: [
          createI18n({
            legacy: false,
            locale: 'en',
            messages: {
              en: {
                auth: {
                  emailRequired: 'Email required',
                  emailPlaceholder: 'Email',
                },
                forgotPassword: {
                  title: 'Forgot Password',
                  submitButton: 'Send',
                  submitting: 'Sending',
                  sendFailed: 'Send failed',
                }
              }
            }
          })
        ]
      }
    })
  }

  it('submits email and shows success message', async () => {
    forgotPasswordMock.mockResolvedValueOnce({ message: 'email sent' })

    const wrapper = mountView()
    await wrapper.get('[data-test="forgot-email"]').setValue('alice@example.com')
    await wrapper.get('[data-test="forgot-submit"]').trigger('click')
    await flushPromises()

    expect(forgotPasswordMock).toHaveBeenCalledWith('alice@example.com')
    expect(wrapper.text()).toContain('email sent')
    expect(toastSuccessMock).toHaveBeenCalledWith('email sent')
  })
})
