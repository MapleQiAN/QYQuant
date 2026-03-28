// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ResetPasswordView from './ResetPasswordView.vue'

const { replaceMock, resetPasswordMock } = vi.hoisted(() => ({
  replaceMock: vi.fn(),
  resetPasswordMock: vi.fn(),
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

describe('ResetPasswordView', () => {
  beforeEach(() => {
    replaceMock.mockReset()
    resetPasswordMock.mockReset()
  })

  it('submits token and new password', async () => {
    resetPasswordMock.mockResolvedValueOnce({ message: 'reset ok' })

    const wrapper = mount(ResetPasswordView)
    await wrapper.get('[data-test="reset-password"]').setValue('NewSecret123!')
    await wrapper.get('[data-test="reset-submit"]').trigger('click')
    await flushPromises()

    expect(resetPasswordMock).toHaveBeenCalledWith('token-123', 'NewSecret123!')
    expect(replaceMock).toHaveBeenCalledWith('/login')
  })
})
