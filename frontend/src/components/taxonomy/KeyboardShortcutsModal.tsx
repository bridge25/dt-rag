// @CODE:TAXONOMY-KEYNAV-002-013
// Modal component for displaying keyboard shortcuts
// WCAG 2.1 AA compliant with focus trap and proper ARIA attributes

import { useEffect } from 'react'
import FocusTrap from 'focus-trap-react'

interface KeyboardShortcutsModalProps {
  isOpen: boolean
  onClose: () => void
}

interface ShortcutItem {
  keys: string
  action: string
  description: string
}

const navigationShortcuts: ShortcutItem[] = [
  {
    keys: 'Tab',
    action: 'Navigate forward',
    description: 'Move focus to next interactive element',
  },
  {
    keys: 'Shift+Tab',
    action: 'Navigate backward',
    description: 'Move focus to previous interactive element',
  },
  {
    keys: 'Arrow keys',
    action: 'Navigate between nodes',
    description: 'Move focus to adjacent taxonomy nodes (spatial and hierarchical)',
  },
]

const actionShortcuts: ShortcutItem[] = [
  {
    keys: '/',
    action: 'Focus search input',
    description: 'Jump to search field to filter taxonomy nodes',
  },
  {
    keys: '+ or =',
    action: 'Zoom in',
    description: 'Increase zoom level of the taxonomy visualization',
  },
  {
    keys: '-',
    action: 'Zoom out',
    description: 'Decrease zoom level of the taxonomy visualization',
  },
  {
    keys: 'L',
    action: 'Toggle layout',
    description: 'Switch between Tree and Radial layout modes',
  },
  {
    keys: 'Home',
    action: 'Focus root node',
    description: 'Jump to the root node of the taxonomy tree',
  },
  {
    keys: '?',
    action: 'Show this help',
    description: 'Display keyboard shortcuts reference (this modal)',
  },
  {
    keys: 'Escape',
    action: 'Close detail panel / Close this help',
    description: 'Exit detail panel or close this shortcuts modal',
  },
]

/**
 * Modal component for displaying keyboard shortcuts reference
 *
 * Features:
 * - Focus trap to contain keyboard navigation within modal
 * - Escape key handler to close modal
 * - WCAG 2.1 AA compliant with role="dialog" and ARIA attributes
 * - Organized shortcuts into Navigation and Actions sections
 *
 * @param isOpen - Whether the modal is visible
 * @param onClose - Callback to close the modal
 */
export default function KeyboardShortcutsModal({
  isOpen,
  onClose,
}: KeyboardShortcutsModalProps) {
  // Handle Escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <FocusTrap
      active={true}
      focusTrapOptions={{
        initialFocus: false,
        fallbackFocus: () => document.body,
        clickOutsideDeactivates: true,
      }}
    >
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
        role="dialog"
        aria-labelledby="shortcuts-title"
        aria-describedby="shortcuts-description"
      >
        <div className="max-h-[80vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 shadow-xl">
          {/* Header */}
          <div className="mb-4 flex items-center justify-between">
            <h2
              id="shortcuts-title"
              className="text-2xl font-bold text-gray-900"
            >
              Keyboard Shortcuts
            </h2>
            <button
              onClick={onClose}
              aria-label="Close keyboard shortcuts"
              className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Description */}
          <p
            id="shortcuts-description"
            className="mb-6 text-sm text-gray-600"
          >
            Use these keyboard shortcuts to navigate and interact with the
            taxonomy tree efficiently.
          </p>

          {/* Shortcuts Content */}
          <div className="space-y-6">
            {/* Navigation Section */}
            <section>
              <h3 className="mb-3 text-lg font-semibold text-gray-800">
                Navigation
              </h3>
              <div className="space-y-2">
                {navigationShortcuts.map((shortcut, index) => (
                  <ShortcutRow key={index} {...shortcut} />
                ))}
              </div>
            </section>

            {/* Actions Section */}
            <section>
              <h3 className="mb-3 text-lg font-semibold text-gray-800">
                Actions
              </h3>
              <div className="space-y-2">
                {actionShortcuts.map((shortcut, index) => (
                  <ShortcutRow key={index} {...shortcut} />
                ))}
              </div>
            </section>
          </div>
        </div>
      </div>
    </FocusTrap>
  )
}

/**
 * Individual shortcut row component
 *
 * @param keys - Keyboard key combination
 * @param action - Brief action name
 * @param description - Detailed description of the action
 */
function ShortcutRow({ keys, action, description }: ShortcutItem) {
  return (
    <div className="flex items-start gap-4">
      <kbd className="min-w-[100px] rounded border border-gray-300 bg-gray-50 px-2 py-1 text-center text-sm font-mono text-gray-700">
        {keys}
      </kbd>
      <div className="flex-1">
        <div className="font-medium text-gray-900">{action}</div>
        <div className="text-sm text-gray-600">{description}</div>
      </div>
    </div>
  )
}
