import '@testing-library/jest-dom'

// Mock ResizeObserver (required by Radix UI)
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
global.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver

// Mock IntersectionObserver (required by some components)
class IntersectionObserverMock {
  root = null
  rootMargin = ''
  thresholds = []
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() { return [] }
}
global.IntersectionObserver = IntersectionObserverMock as unknown as typeof IntersectionObserver

// Mock window.matchMedia (required by Radix UI)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

// Mock scrollTo (required by some components)
Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: () => {},
})

// Mock HTMLElement.scrollIntoView
Element.prototype.scrollIntoView = () => {}
