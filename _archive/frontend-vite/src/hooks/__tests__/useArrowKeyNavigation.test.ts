/**
 * Test file
 *
 * @CODE:FRONTEND-001
 */

// @TEST:TAXONOMY-KEYNAV-002-007
// Tests for useArrowKeyNavigation hook

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useArrowKeyNavigation } from '../useArrowKeyNavigation'
import { useFocusManagement } from '../useFocusManagement'
import type { Node } from '@xyflow/react'
import type { TaxonomyNode } from '../../lib/api/types'

// Mock useFocusManagement
vi.mock('../useFocusManagement')

interface FlowNode extends Node {
  data: {
    taxonomyNode: TaxonomyNode
    isExpanded: boolean
  }
}

const mockSetFocus = vi.fn()

const createMockNode = (id: string, x: number, y: number, parentId: string | null = null): FlowNode => ({
  id,
  type: 'taxonomyNode',
  position: { x, y },
  data: {
    taxonomyNode: {
      id,
      name: `Node ${id}`,
      path: [`node-${id}`],
      parent_id: parentId,
      level: 0,
      document_count: 0,
    },
    isExpanded: true,
  },
})

describe('useArrowKeyNavigation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useFocusManagement).mockReturnValue({
      focusedNodeId: 'node-1',
      setFocus: mockSetFocus,
      restoreFocus: vi.fn(),
      clearFocus: vi.fn(),
    })
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  it('should initialize without errors', () => {
    const nodes: FlowNode[] = [
      createMockNode('node-1', 0, 0),
      createMockNode('node-2', 100, 0),
    ]

    const { result } = renderHook(() => useArrowKeyNavigation(nodes, 'tree'))

    expect(result.current).toBeDefined()
    expect(result.current.handleArrowKey).toBeInstanceOf(Function)
  })

  it('should return handleArrowKey function', () => {
    const nodes: FlowNode[] = [createMockNode('node-1', 0, 0)]

    const { result } = renderHook(() => useArrowKeyNavigation(nodes, 'tree'))

    expect(typeof result.current.handleArrowKey).toBe('function')
  })

  it('should call setFocus when handleArrowKey is invoked with right direction', () => {
    const nodes: FlowNode[] = [
      createMockNode('node-1', 0, 0),
      createMockNode('node-2', 100, 0),
    ]

    const { result } = renderHook(() => useArrowKeyNavigation(nodes, 'tree'))

    act(() => {
      result.current.handleArrowKey('right')
    })

    // setFocus should be called (implementation will determine the target node)
    expect(mockSetFocus).toHaveBeenCalled()
  })

  it('should handle arrow up direction', () => {
    const nodes: FlowNode[] = [
      createMockNode('node-1', 0, 100),
      createMockNode('node-2', 0, 0),
    ]

    const { result } = renderHook(() => useArrowKeyNavigation(nodes, 'tree'))

    act(() => {
      result.current.handleArrowKey('up')
    })

    expect(mockSetFocus).toHaveBeenCalled()
  })

  it('should handle arrow down direction', () => {
    const nodes: FlowNode[] = [
      createMockNode('node-1', 0, 0),
      createMockNode('node-2', 0, 100),
    ]

    const { result } = renderHook(() => useArrowKeyNavigation(nodes, 'tree'))

    act(() => {
      result.current.handleArrowKey('down')
    })

    expect(mockSetFocus).toHaveBeenCalled()
  })

  it('should handle arrow left direction', () => {
    const nodes: FlowNode[] = [
      createMockNode('node-1', 100, 0),
      createMockNode('node-2', 0, 0),
    ]

    const { result } = renderHook(() => useArrowKeyNavigation(nodes, 'tree'))

    act(() => {
      result.current.handleArrowKey('left')
    })

    expect(mockSetFocus).toHaveBeenCalled()
  })

  it('should listen for keyboard events when hook is mounted', () => {
    const addEventListenerSpy = vi.spyOn(window, 'addEventListener')
    const nodes: FlowNode[] = [createMockNode('node-1', 0, 0)]

    renderHook(() => useArrowKeyNavigation(nodes, 'tree'))

    expect(addEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function))
  })

  it('should cleanup event listeners on unmount', () => {
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')
    const nodes: FlowNode[] = [createMockNode('node-1', 0, 0)]

    const { unmount } = renderHook(() => useArrowKeyNavigation(nodes, 'tree'))

    unmount()

    expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function))
  })

  it('should not call setFocus when no adjacent node exists', () => {
    const nodes: FlowNode[] = [createMockNode('node-1', 0, 0)]

    const { result } = renderHook(() => useArrowKeyNavigation(nodes, 'tree'))

    act(() => {
      result.current.handleArrowKey('right')
    })

    // Should not call setFocus when there's no node to the right
    expect(mockSetFocus).not.toHaveBeenCalled()
  })
})
