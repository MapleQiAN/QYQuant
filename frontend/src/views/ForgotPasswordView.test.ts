// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ForgotPasswordView from './ForgotPasswordView.vue'

const { forgotPasswordMock } = vi.hoisted(() => ({
  forgotPasswordMock: vi.fn(),
}))

vi.mock('../api/auth', () => ({
  forgotPassword: forgotPasswordMock,
}))

describe('ForgotPasswordView', () => {
  beforeEach(() => {
    forgotPasswordMock.mockReset()
  })

  it('submits email and shows success message', async () => {
    forgotPasswordMock.mockResolvedValueOnce({ message: 'email sent' })

    const wrapper = mount(ForgotPasswordView)
    await wrapper.get('[data-test="forgot-email"]').setValue('alice@example.com')
    await wrapper.get('[data-test="forgot-submit"]').trigger('click')
    await flushPromises()

    expect(forgotPasswordMock).toHaveBeenCalledWith('alice@example.com')
    expect(wrapper.text()).toContain('email sent')
  })
})
