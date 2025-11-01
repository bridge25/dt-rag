// @CODE:TAXONOMY-KEYNAV-002-011
// Hook for managing keyboard shortcuts in taxonomy visualization
// Uses react-hotkeys-hook for robust shortcut handling with scope awareness

import { useHotkeys } from 'react-hotkeys-hook'
import { useFocusManagement } from './useFocusManagement'
import { useTaxonomyStore } from '../stores/useTaxonomyStore'

interface UseKeyboardShortcutsProps {
  onZoomIn: () => void
  onZoomOut: () => void
  onToggleLayout: () => void
  onShowHelp: () => void
  rootNodeId?: string
}

/**
 * Hook for managing keyboard shortcuts in taxonomy tree visualization
 *
 * Provides shortcuts for:
 * - / : Focus search input
 * - +, = : Zoom in
 * - - : Zoom out
 * - L : Toggle layout (Tree ↔ Radial)
 * - Home : Focus root node
 * - ? (Shift+/) : Show keyboard shortcuts help modal
 *
 * Shortcuts are only active when keyboardMode === 'navigation'
 *
 * @param props - Callback functions and optional root node ID
 */
export function useKeyboardShortcuts({
  onZoomIn,
  onZoomOut,
  onToggleLayout,
  onShowHelp,
  rootNodeId,
}: UseKeyboardShortcutsProps) {
  const { setFocus } = useFocusManagement()
  const keyboardMode = useTaxonomyStore((state) => state.keyboardMode)
  const enabled = keyboardMode === 'navigation'

  // Search focus shortcut
  useHotkeys(
    '/',
    () => {
      const searchInput = document.querySelector(
        'input[aria-label="Search taxonomy nodes"]'
      )
      if (searchInput instanceof HTMLInputElement) {
        searchInput.focus()
      }
    },
    { enabled, preventDefault: true }
  )

  // Zoom in shortcuts (+, =)
  // Note: + requires Shift key, so we use shift+= for +
  useHotkeys('shift+=,=', onZoomIn, { enabled, preventDefault: true })

  // Zoom out shortcut (-)
  useHotkeys('-', onZoomOut, { enabled, preventDefault: true })

  // Layout toggle shortcut (L)
  useHotkeys('l', onToggleLayout, { enabled, preventDefault: true })

  // Home shortcut - focus root node
  useHotkeys(
    'home',
    () => {
      if (rootNodeId) {
        setFocus(rootNodeId)
      }
    },
    { enabled, preventDefault: true }
  )

  // Help modal shortcut (Shift+/)
  useHotkeys('shift+/', onShowHelp, { enabled, preventDefault: true })
}
