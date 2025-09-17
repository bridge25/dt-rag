import { useMemo, useCallback, useRef, useEffect } from 'react'

// 메모리 최적화를 위한 WeakMap 캐시
const nodeDisplayCache = new WeakMap()
const expandedStateCache = new Map()

// 메모리 사용량 모니터링
export function useMemoryMonitor() {
  const memoryRef = useRef({ peak: 0, current: 0 })

  const checkMemory = useCallback(() => {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      memoryRef.current.current = memory.usedJSHeapSize
      memoryRef.current.peak = Math.max(memoryRef.current.peak, memory.usedJSHeapSize)
    }
  }, [])

  useEffect(() => {
    const interval = setInterval(checkMemory, 1000)
    return () => clearInterval(interval)
  }, [checkMemory])

  return memoryRef.current
}

// 가상화를 위한 노드 캐싱
export function useNodeCache<T extends { node_id: string }>(nodes: T[]) {
  return useMemo(() => {
    const cache = new Map<string, T>()
    nodes.forEach(node => {
      cache.set(node.node_id, node)
    })
    return cache
  }, [nodes])
}

// 렌더링 최적화를 위한 디바운스
export function useDebounceCallback<T extends any[]>(
  callback: (...args: T) => void,
  delay: number
) {
  const timeoutRef = useRef<NodeJS.Timeout>()

  return useCallback((...args: T) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    timeoutRef.current = setTimeout(() => {
      callback(...args)
    }, delay)
  }, [callback, delay])
}

// 대량 데이터 처리를 위한 청크 처리
export function useChunkedProcessing<T>(
  data: T[],
  chunkSize: number = 1000,
  processChunk: (chunk: T[]) => void
) {
  const processedRef = useRef(0)

  const processNext = useCallback(() => {
    if (processedRef.current >= data.length) return

    const chunk = data.slice(processedRef.current, processedRef.current + chunkSize)
    processChunk(chunk)
    processedRef.current += chunkSize

    if (processedRef.current < data.length) {
      // 다음 청크를 비동기로 처리하여 UI 블로킹 방지
      setTimeout(processNext, 0)
    }
  }, [data, chunkSize, processChunk])

  useEffect(() => {
    processedRef.current = 0
    processNext()
  }, [processNext])

  return {
    progress: Math.min(processedRef.current / data.length, 1),
    isComplete: processedRef.current >= data.length
  }
}

// 확장 상태 최적화
export function useOptimizedExpandedState(initialState: Set<string> = new Set()) {
  const stateRef = useRef(initialState)

  const toggle = useCallback((nodeId: string) => {
    const current = stateRef.current
    const newSet = new Set(current)

    if (newSet.has(nodeId)) {
      newSet.delete(nodeId)
      expandedStateCache.delete(nodeId)
    } else {
      newSet.add(nodeId)
      expandedStateCache.set(nodeId, true)
    }

    stateRef.current = newSet
    return newSet
  }, [])

  const has = useCallback((nodeId: string) => {
    return stateRef.current.has(nodeId)
  }, [])

  const clear = useCallback(() => {
    stateRef.current = new Set()
    expandedStateCache.clear()
  }, [])

  return {
    toggle,
    has,
    clear,
    size: stateRef.current.size
  }
}

// 성능 메트릭 수집
export function usePerformanceMetrics() {
  const metricsRef = useRef({
    renderCount: 0,
    lastRenderTime: 0,
    averageRenderTime: 0,
    totalRenderTime: 0
  })

  const startMeasure = useCallback(() => {
    return performance.now()
  }, [])

  const endMeasure = useCallback((startTime: number) => {
    const endTime = performance.now()
    const renderTime = endTime - startTime

    metricsRef.current.renderCount++
    metricsRef.current.lastRenderTime = renderTime
    metricsRef.current.totalRenderTime += renderTime
    metricsRef.current.averageRenderTime =
      metricsRef.current.totalRenderTime / metricsRef.current.renderCount

    // 200ms 이상 걸리면 경고 로그
    if (renderTime > 200) {
      console.warn(`Slow render detected: ${renderTime.toFixed(2)}ms`)
    }
  }, [])

  return {
    metrics: metricsRef.current,
    startMeasure,
    endMeasure
  }
}

// 접근성을 위한 포커스 관리
export function useFocusManagement() {
  const focusedIndexRef = useRef(0)
  const containerRef = useRef<HTMLElement>()

  const setFocusedIndex = useCallback((index: number) => {
    focusedIndexRef.current = index
  }, [])

  const getFocusedIndex = useCallback(() => {
    return focusedIndexRef.current
  }, [])

  const focusItem = useCallback((index: number) => {
    const container = containerRef.current
    if (!container) return

    const items = container.querySelectorAll('[role="treeitem"]')
    const item = items[index] as HTMLElement
    if (item) {
      item.focus()
      focusedIndexRef.current = index
    }
  }, [])

  const moveFocus = useCallback((direction: 'up' | 'down' | 'home' | 'end', maxIndex: number) => {
    const current = focusedIndexRef.current
    let newIndex = current

    switch (direction) {
      case 'up':
        newIndex = Math.max(0, current - 1)
        break
      case 'down':
        newIndex = Math.min(maxIndex - 1, current + 1)
        break
      case 'home':
        newIndex = 0
        break
      case 'end':
        newIndex = maxIndex - 1
        break
    }

    focusItem(newIndex)
  }, [focusItem])

  return {
    focusedIndex: focusedIndexRef.current,
    setFocusedIndex,
    getFocusedIndex,
    focusItem,
    moveFocus,
    containerRef
  }
}