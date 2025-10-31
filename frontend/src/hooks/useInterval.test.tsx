// @TEST:FRONTEND-INTEGRATION-001:PHASE3:INTERVAL-HOOK
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useInterval } from './useInterval'

describe('useInterval', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should call callback at specified interval', () => {
    const callback = vi.fn()

    renderHook(() => useInterval(callback, 1000))

    expect(callback).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1000)
    expect(callback).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(1000)
    expect(callback).toHaveBeenCalledTimes(2)

    vi.advanceTimersByTime(1000)
    expect(callback).toHaveBeenCalledTimes(3)
  })

  it('should not call callback when delay is null', () => {
    const callback = vi.fn()

    renderHook(() => useInterval(callback, null))

    vi.advanceTimersByTime(5000)

    expect(callback).not.toHaveBeenCalled()
  })

  it('should update callback without restarting interval', () => {
    const callback1 = vi.fn()
    const callback2 = vi.fn()

    const { rerender } = renderHook(
      ({ cb }) => useInterval(cb, 1000),
      { initialProps: { cb: callback1 } }
    )

    vi.advanceTimersByTime(1000)
    expect(callback1).toHaveBeenCalledTimes(1)
    expect(callback2).not.toHaveBeenCalled()

    rerender({ cb: callback2 })

    vi.advanceTimersByTime(1000)
    expect(callback1).toHaveBeenCalledTimes(1)
    expect(callback2).toHaveBeenCalledTimes(1)
  })

  it('should cleanup interval on unmount', () => {
    const callback = vi.fn()

    const { unmount } = renderHook(() => useInterval(callback, 1000))

    vi.advanceTimersByTime(1000)
    expect(callback).toHaveBeenCalledTimes(1)

    unmount()

    vi.advanceTimersByTime(5000)
    expect(callback).toHaveBeenCalledTimes(1)
  })

  it('should restart interval when delay changes', () => {
    const callback = vi.fn()

    const { rerender } = renderHook(
      ({ delay }) => useInterval(callback, delay),
      { initialProps: { delay: 1000 } }
    )

    vi.advanceTimersByTime(1000)
    expect(callback).toHaveBeenCalledTimes(1)

    rerender({ delay: 500 })

    vi.advanceTimersByTime(500)
    expect(callback).toHaveBeenCalledTimes(2)

    vi.advanceTimersByTime(500)
    expect(callback).toHaveBeenCalledTimes(3)
  })
})
