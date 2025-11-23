/**
 * Hook for arrow key navigation in taxonomy visualization
 *
 * @CODE:FRONTEND-MIGRATION-001
 */

"use client"

import { useCallback, useEffect } from "react"
import { useFocusManagement } from "./useFocusManagement"
import { findAdjacentNode, type Direction, type FlowNode } from "@/lib/utils/findAdjacentNode"
import type { LayoutType } from "@/components/taxonomy/taxonomyLayouts"

/**
 * Hook for managing arrow key navigation between taxonomy nodes
 *
 * Provides handleArrowKey function to navigate to adjacent nodes based on
 * spatial positioning and tree hierarchy. Listens for keyboard events and
 * integrates with focus management system.
 *
 * @param nodes - Array of flow nodes with taxonomy data
 * @param currentLayout - Current layout type (tree or radial)
 * @returns Object with handleArrowKey function
 */
export function useArrowKeyNavigation(nodes: FlowNode[], currentLayout: LayoutType) {
  const { focusedNodeId, setFocus } = useFocusManagement()

  /**
   * Handle arrow key navigation to adjacent node
   *
   * @param direction - Direction to navigate (up, down, left, right)
   */
  const handleArrowKey = useCallback(
    (direction: Direction) => {
      if (!focusedNodeId) {
        return
      }

      // Find adjacent node using spatial algorithm
      const targetNodeId = findAdjacentNode(focusedNodeId, direction, nodes, currentLayout)

      if (targetNodeId) {
        setFocus(targetNodeId)
      }
    },
    [focusedNodeId, nodes, currentLayout, setFocus]
  )

  /**
   * Keyboard event handler for arrow keys
   */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Map ArrowKey events to direction
      const keyToDirection: Record<string, Direction> = {
        ArrowUp: "up",
        ArrowDown: "down",
        ArrowLeft: "left",
        ArrowRight: "right",
      }

      const direction = keyToDirection[event.key]
      if (direction) {
        event.preventDefault()
        handleArrowKey(direction)
      }
    }

    window.addEventListener("keydown", handleKeyDown)

    return () => {
      window.removeEventListener("keydown", handleKeyDown)
    }
  }, [handleArrowKey])

  return {
    handleArrowKey,
  }
}
