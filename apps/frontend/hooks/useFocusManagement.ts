/**
 * Hook for managing focus state and history in taxonomy visualization
 *
 * @CODE:FRONTEND-MIGRATION-001
 */

"use client"

import { useCallback } from "react"
import { useTaxonomyStore } from "@/stores/useTaxonomyStore"

/**
 * Hook for managing focus state and history in taxonomy visualization
 *
 * Provides functions to set focus, restore previous focus (Escape key),
 * and clear focus state. Uses Zustand store for centralized state management.
 *
 * @returns Focus management functions and current focused node ID
 */
export function useFocusManagement() {
  const focusedNodeId = useTaxonomyStore((state) => state.focusedNodeId)
  const setFocusedNode = useTaxonomyStore((state) => state.setFocusedNode)
  const pushFocusHistory = useTaxonomyStore((state) => state.pushFocusHistory)
  const popFocusHistory = useTaxonomyStore((state) => state.popFocusHistory)
  const clearFocusHistory = useTaxonomyStore((state) => state.clearFocusHistory)

  /**
   * Set focus to a node and save to history
   * @param nodeId - Node ID to focus, or null to clear focus
   */
  const setFocus = useCallback(
    (nodeId: string | null) => {
      if (nodeId) {
        pushFocusHistory(nodeId)
      }
      setFocusedNode(nodeId)
    },
    [setFocusedNode, pushFocusHistory]
  )

  /**
   * Restore focus to previous node from history (for Escape key)
   */
  const restoreFocus = useCallback(() => {
    const previousNode = popFocusHistory()
    if (previousNode) {
      setFocusedNode(previousNode)
    }
  }, [popFocusHistory, setFocusedNode])

  /**
   * Clear focus and all history
   */
  const clearFocus = useCallback(() => {
    setFocusedNode(null)
    clearFocusHistory()
  }, [setFocusedNode, clearFocusHistory])

  return {
    focusedNodeId,
    setFocus,
    restoreFocus,
    clearFocus,
  }
}
