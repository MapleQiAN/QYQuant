// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import SimulationChart from './SimulationChart.vue'

const { initMock, setOptionMock, resizeMock, disposeMock } = vi.hoisted(() => ({
  setOptionMock: vi.fn(),
  resizeMock: vi.fn(),
  disposeMock: vi.fn(),
  initMock: vi.fn(),
}))

vi.mock('echarts', () => ({
  init: initMock,
}))

class ResizeObserverMock {
  observe = vi.fn()
  disconnect = vi.fn()
}

describe('SimulationChart', () => {
  beforeEach(() => {
    setOptionMock.mockClear()
    resizeMock.mockClear()
    disposeMock.mockClear()
    initMock.mockClear()
    initMock.mockReturnValue({
      setOption: setOptionMock,
      resize: resizeMock,
      dispose: disposeMock,
    })
    vi.stubGlobal('ResizeObserver', ResizeObserverMock)
  })

  it('shows empty hint when records are empty', () => {
    const wrapper = mount(SimulationChart, {
      props: {
        records: [],
      },
    })

    expect(wrapper.text()).toContain('暂无收益曲线数据')
  })

  it('initializes echarts when records are provided', async () => {
    mount(SimulationChart, {
      props: {
        records: [
          {
            trade_date: '2026-03-20',
            equity: '105000.00',
            cash: '55000.00',
            daily_return: '0.000500',
          },
        ],
      },
    })
    await nextTick()

    expect(initMock).toHaveBeenCalledTimes(1)
    expect(setOptionMock).toHaveBeenCalled()
  })
})
