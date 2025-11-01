// @TEST:TAXONOMY-KEYNAV-002-001
// Test for TAG-001: Zustand Store Setup for Keyboard Navigation

import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTaxonomyStore } from './useTaxonomyStore'

describe('useTaxonomyStore - Focus Management', () => {
  beforeEach(() => {
    // Reset store state before each test
    const { getState } = useTaxonomyStore
    act(() => {
      getState().setFocusedNode(null)
      getState().clearFocusHistory()
    })
  })

  it('should initialize with focusedNodeId as null', () => {
    const { result } = renderHook(() => useTaxonomyStore())
    expect(result.current.focusedNodeId).toBeNull()
  })

  it('should initialize with empty focusHistory', () => {
    const { result } = renderHook(() => useTaxonomyStore())
    expect(result.current.focusHistory).toEqual([])
  })

  it('should initialize with keyboardMode as navigation', () => {
    const { result } = renderHook(() => useTaxonomyStore())
    expect(result.current.keyboardMode).toBe('navigation')
  })

  it('should set focusedNode via setFocusedNode action', () => {
    const { result } = renderHook(() => useTaxonomyStore())

    act(() => {
      result.current.setFocusedNode('node-123')
    })

    expect(result.current.focusedNodeId).toBe('node-123')
  })

  it('should allow clearing focusedNode by setting to null', () => {
    const { result } = renderHook(() => useTaxonomyStore())

    act(() => {
      result.current.setFocusedNode('node-123')
      result.current.setFocusedNode(null)
    })

    expect(result.current.focusedNodeId).toBeNull()
  })

  it('should push node to focusHistory via pushFocusHistory', () => {
    const { result } = renderHook(() => useTaxonomyStore())

    act(() => {
      result.current.pushFocusHistory('node-1')
    })

    expect(result.current.focusHistory).toEqual(['node-1'])
  })

  it('should push multiple nodes to focusHistory', () => {
    const { result } = renderHook(() => useTaxonomyStore())

    act(() => {
      result.current.pushFocusHistory('node-1')
      result.current.pushFocusHistory('node-2')
      result.current.pushFocusHistory('node-3')
    })

    expect(result.current.focusHistory).toEqual(['node-1', 'node-2', 'node-3'])
  })

  it('should pop last node from focusHistory via popFocusHistory', () => {
    const { result } = renderHook(() => useTaxonomyStore())

    act(() => {
      result.current.pushFocusHistory('node-1')
      result.current.pushFocusHistory('node-2')
    })

    let poppedNode: string | null = null
    act(() => {
      poppedNode = result.current.popFocusHistory()
    })

    expect(poppedNode).toBe('node-2')
    expect(result.current.focusHistory).toEqual(['node-1'])
  })

  it('should return null when popping from empty focusHistory', () => {
    const { result } = renderHook(() => useTaxonomyStore())

    let poppedNode: string | null = null
    act(() => {
      poppedNode = result.current.popFocusHistory()
    })

    expect(poppedNode).toBeNull()
  })

  it('should clear all focusHistory via clearFocusHistory', () => {
    const { result } = renderHook(() => useTaxonomyStore())

    act(() => {
      result.current.pushFocusHistory('node-1')
      result.current.pushFocusHistory('node-2')
      result.current.clearFocusHistory()
    })

    expect(result.current.focusHistory).toEqual([])
  })

  it('should set keyboardMode via setKeyboardMode', () => {
    const { result } = renderHook(() => useTaxonomyStore())

    act(() => {
      result.current.setKeyboardMode('search')
    })

    expect(result.current.keyboardMode).toBe('search')
  })

  it('should change keyboardMode from navigation to panel', () => {
    const { result } = renderHook(() => useTaxonomyStore())

    act(() => {
      result.current.setKeyboardMode('panel')
    })

    expect(result.current.keyboardMode).toBe('panel')
  })

  it('should allow resetting keyboardMode back to navigation', () => {
    const { result } = renderHook(() => useTaxonomyStore())

    act(() => {
      result.current.setKeyboardMode('search')
      result.current.setKeyboardMode('navigation')
    })

    expect(result.current.keyboardMode).toBe('navigation')
  })
})
