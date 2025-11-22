/**
 * Zustand store for taxonomy visualization and keyboard navigation state management
 *
 * @CODE:FRONTEND-MIGRATION-001
 */

"use client"

import { create } from "zustand"

/**
 * Keyboard interaction mode for taxonomy visualization
 * - navigation: Arrow keys move between nodes
 * - search: Arrow keys disabled (text editing)
 * - panel: Focus trapped within detail panel
 */
export type KeyboardMode = "navigation" | "search" | "panel"

/**
 * Taxonomy store with keyboard navigation state management
 */
interface TaxonomyStore {
  // Focus management state
  /**
   * ID of currently focused node, null if no node focused
   */
  focusedNodeId: string | null

  /**
   * Stack of previously focused nodes for Escape key restoration
   */
  focusHistory: string[]

  /**
   * Current keyboard interaction mode
   */
  keyboardMode: KeyboardMode

  // Actions
  /**
   * Set the currently focused node
   * @param id - Node ID to focus, or null to clear focus
   */
  setFocusedNode: (id: string | null) => void

  /**
   * Push a node ID to focus history stack
   * @param id - Node ID to save in history
   */
  pushFocusHistory: (id: string) => void

  /**
   * Pop the last node ID from focus history stack
   * @returns The popped node ID, or null if history is empty
   */
  popFocusHistory: () => string | null

  /**
   * Clear all focus history
   */
  clearFocusHistory: () => void

  /**
   * Set the keyboard interaction mode
   * @param mode - The keyboard mode to activate
   */
  setKeyboardMode: (mode: KeyboardMode) => void
}

export const useTaxonomyStore = create<TaxonomyStore>((set, get) => ({
  // Initial state
  focusedNodeId: null,
  focusHistory: [],
  keyboardMode: "navigation",

  // Actions
  setFocusedNode: (id) => set({ focusedNodeId: id }),

  pushFocusHistory: (id) =>
    set((state) => ({
      focusHistory: [...state.focusHistory, id],
    })),

  popFocusHistory: () => {
    const { focusHistory } = get()
    if (focusHistory.length === 0) {
      return null
    }

    const lastNode = focusHistory[focusHistory.length - 1]
    set({
      focusHistory: focusHistory.slice(0, -1),
    })
    return lastNode
  },

  clearFocusHistory: () => set({ focusHistory: [] }),

  setKeyboardMode: (mode) => set({ keyboardMode: mode }),
}))
