// @TEST:TAXONOMY-KEYNAV-002-002
// Test for TAG-002: useFocusManagement Hook

import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useFocusManagement } from './useFocusManagement'
import { useTaxonomyStore } from '../stores/useTaxonomyStore'

describe('useFocusManagement', () => {
  beforeEach(() => {
    // Reset store state before each test
    const { getState } = useTaxonomyStore
    act(() => {
      getState().setFocusedNode(null)
      getState().clearFocusHistory()
    })
  })

  describe('setFocus', () => {
    it('should set focused node and push to history', () => {
      const { result } = renderHook(() => useFocusManagement())

      act(() => {
        result.current.setFocus('node-123')
      })

      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).toBe('node-123')
      expect(store.focusHistory).toContain('node-123')
    })

    it('should update focused node when called multiple times', () => {
      const { result } = renderHook(() => useFocusManagement())

      act(() => {
        result.current.setFocus('node-1')
        result.current.setFocus('node-2')
      })

      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).toBe('node-2')
      expect(store.focusHistory).toEqual(['node-1', 'node-2'])
    })

    it('should handle null nodeId to clear focus', () => {
      const { result } = renderHook(() => useFocusManagement())

      act(() => {
        result.current.setFocus('node-123')
        result.current.setFocus(null)
      })

      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).toBeNull()
    })
  })

  describe('restoreFocus', () => {
    it('should restore focus to previous node from history', () => {
      const { result } = renderHook(() => useFocusManagement())

      act(() => {
        result.current.setFocus('node-1')
        result.current.setFocus('node-2')
        result.current.setFocus('node-3')
      })

      act(() => {
        result.current.restoreFocus()
      })

      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).toBe('node-3')
      expect(store.focusHistory).toEqual(['node-1', 'node-2'])
    })

    it('should handle restoring when history has only one item', () => {
      const { result } = renderHook(() => useFocusManagement())

      act(() => {
        result.current.setFocus('node-1')
      })

      act(() => {
        result.current.restoreFocus()
      })

      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).toBe('node-1')
      expect(store.focusHistory).toEqual([])
    })

    it('should do nothing when history is empty', () => {
      const { result } = renderHook(() => useFocusManagement())

      act(() => {
        result.current.restoreFocus()
      })

      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).toBeNull()
      expect(store.focusHistory).toEqual([])
    })
  })

  describe('clearFocus', () => {
    it('should clear focused node and history', () => {
      const { result } = renderHook(() => useFocusManagement())

      act(() => {
        result.current.setFocus('node-1')
        result.current.setFocus('node-2')
      })

      act(() => {
        result.current.clearFocus()
      })

      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).toBeNull()
      expect(store.focusHistory).toEqual([])
    })

    it('should work when focus is already clear', () => {
      const { result } = renderHook(() => useFocusManagement())

      act(() => {
        result.current.clearFocus()
      })

      const store = useTaxonomyStore.getState()
      expect(store.focusedNodeId).toBeNull()
      expect(store.focusHistory).toEqual([])
    })
  })

  describe('focusedNodeId', () => {
    it('should return current focusedNodeId from store', () => {
      const { result } = renderHook(() => useFocusManagement())

      act(() => {
        result.current.setFocus('node-abc')
      })

      expect(result.current.focusedNodeId).toBe('node-abc')
    })

    it('should return null when no node is focused', () => {
      const { result } = renderHook(() => useFocusManagement())

      expect(result.current.focusedNodeId).toBeNull()
    })
  })

  describe('useCallback memoization', () => {
    it('should return stable function references', () => {
      const { result, rerender } = renderHook(() => useFocusManagement())

      const firstSetFocus = result.current.setFocus
      const firstRestoreFocus = result.current.restoreFocus
      const firstClearFocus = result.current.clearFocus

      rerender()

      expect(result.current.setFocus).toBe(firstSetFocus)
      expect(result.current.restoreFocus).toBe(firstRestoreFocus)
      expect(result.current.clearFocus).toBe(firstClearFocus)
    })
  })
})
