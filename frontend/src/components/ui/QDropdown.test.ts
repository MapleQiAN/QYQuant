import { describe, expect, it, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import QDropdown from './QDropdown.vue'

function rect({
  left = 0,
  top = 0,
  width = 0,
  height = 0,
}: {
  left?: number
  top?: number
  width?: number
  height?: number
}) {
  return {
    left,
    top,
    width,
    height,
    right: left + width,
    bottom: top + height,
    x: left,
    y: top,
    toJSON: () => ({}),
  }
}

describe('QDropdown', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('clamps a start-aligned panel inside the viewport', async () => {
    Object.defineProperty(window, 'innerWidth', {
      value: 260,
      configurable: true,
      writable: true,
    })

    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(function () {
      if (this.classList.contains('q-dropdown')) {
        return rect({ left: 220, top: 20, width: 24, height: 24 }) as DOMRect
      }

      if (this.classList.contains('q-dropdown__panel')) {
        return rect({ left: 220, top: 50, width: 320, height: 180 }) as DOMRect
      }

      return rect({ width: 24, height: 24 }) as DOMRect
    })

    const wrapper = mount(QDropdown, {
      props: {
        placement: 'bottom-start',
        items: [
          {
            key: 'profile',
            label: 'Very long dropdown label that should stay inside the viewport',
          },
        ],
      },
      slots: {
        trigger: '<button type="button">Open</button>',
      },
    })

    await wrapper.get('.q-dropdown__trigger').trigger('click')
    await nextTick()

    const panel = wrapper.get('.q-dropdown__panel').element as HTMLElement

    expect(panel.style.maxWidth).toBe('236px')
    expect(panel.style.getPropertyValue('--q-dropdown-offset-x')).toBe('-208px')
  })

  it('limits an end-aligned panel width near the viewport edge', async () => {
    Object.defineProperty(window, 'innerWidth', {
      value: 260,
      configurable: true,
      writable: true,
    })

    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(function () {
      if (this.classList.contains('q-dropdown')) {
        return rect({ left: 220, top: 20, width: 24, height: 24 }) as DOMRect
      }

      if (this.classList.contains('q-dropdown__panel')) {
        return rect({ left: -156, top: 50, width: 400, height: 180 }) as DOMRect
      }

      return rect({ width: 24, height: 24 }) as DOMRect
    })

    const wrapper = mount(QDropdown, {
      props: {
        placement: 'bottom-end',
        items: [
          {
            key: 'profile',
            label: 'Very long dropdown label that should stay inside the viewport',
          },
        ],
      },
      slots: {
        trigger: '<button type="button">Open</button>',
      },
    })

    await wrapper.get('.q-dropdown__trigger').trigger('click')
    await nextTick()

    const panel = wrapper.get('.q-dropdown__panel').element as HTMLElement

    expect(panel.style.maxWidth).toBe('236px')
    expect(panel.style.getPropertyValue('--q-dropdown-offset-x')).toBe('4px')
  })

  it('adds match-width class and skips JS positioning when matchWidth is true', async () => {
    Object.defineProperty(window, 'innerWidth', {
      value: 800,
      configurable: true,
      writable: true,
    })

    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(function () {
      if (this.classList.contains('q-dropdown')) {
        return rect({ left: 100, top: 20, width: 200, height: 40 }) as DOMRect
      }

      if (this.classList.contains('q-dropdown__panel')) {
        return rect({ left: 100, top: 66, width: 180, height: 100 }) as DOMRect
      }

      return rect({ width: 200, height: 40 }) as DOMRect
    })

    const wrapper = mount(QDropdown, {
      props: {
        matchWidth: true,
        placement: 'bottom-start',
        items: [{ key: 'a', label: 'Item A' }],
      },
      slots: {
        trigger: '<button type="button">Open</button>',
      },
    })

    await wrapper.get('.q-dropdown__trigger').trigger('click')
    await nextTick()

    const panel = wrapper.get('.q-dropdown__panel')

    // CSS class drives the width, not inline styles
    expect(panel.classes()).toContain('q-dropdown__panel--match-width')
    expect((panel.element as HTMLElement).style.width).toBe('')
    expect((panel.element as HTMLElement).style.maxWidth).toBe('')
    expect((panel.element as HTMLElement).style.minWidth).toBe('')
  })

  it('does not add match-width class when matchWidth is false', async () => {
    Object.defineProperty(window, 'innerWidth', {
      value: 800,
      configurable: true,
      writable: true,
    })

    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(function () {
      if (this.classList.contains('q-dropdown')) {
        return rect({ left: 100, top: 20, width: 200, height: 40 }) as DOMRect
      }

      if (this.classList.contains('q-dropdown__panel')) {
        return rect({ left: 100, top: 66, width: 180, height: 100 }) as DOMRect
      }

      return rect({ width: 200, height: 40 }) as DOMRect
    })

    const wrapper = mount(QDropdown, {
      props: {
        matchWidth: false,
        placement: 'bottom-start',
        items: [{ key: 'a', label: 'Item A' }],
      },
      slots: {
        trigger: '<button type="button">Open</button>',
      },
    })

    await wrapper.get('.q-dropdown__trigger').trigger('click')
    await nextTick()

    const panel = wrapper.get('.q-dropdown__panel')

    expect(panel.classes()).not.toContain('q-dropdown__panel--match-width')
  })
})
