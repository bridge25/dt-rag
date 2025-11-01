// @TEST:TAXONOMY-KEYNAV-002-011
import { renderHook, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useKeyboardShortcuts } from '../useKeyboardShortcuts'
import { useTaxonomyStore } from '../../stores/useTaxonomyStore'
import { useFocusManagement } from '../useFocusManagement'
import userEvent from '@testing-library/user-event'

// Mock dependencies
vi.mock('../useFocusManagement')
vi.mock('../../stores/useTaxonomyStore')

describe('useKeyboardShortcuts', () => {
  const mockSetFocus = vi.fn()
  const mockOnZoomIn = vi.fn()
  const mockOnZoomOut = vi.fn()
  const mockOnToggleLayout = vi.fn()
  const mockOnShowHelp = vi.fn()
  let user: ReturnType<typeof userEvent.setup>

  beforeEach(() => {
    vi.clearAllMocks()
    user = userEvent.setup()

    // Mock useFocusManagement
    vi.mocked(useFocusManagement).mockReturnValue({
      focusedNodeId: null,
      setFocus: mockSetFocus,
      restoreFocus: vi.fn(),
      clearFocus: vi.fn(),
    })

    // Mock useTaxonomyStore with navigation mode enabled by default
    vi.mocked(useTaxonomyStore).mockReturnValue('navigation')
  })

  afterEach(() => {
    // Clean up any DOM elements
    document.body.innerHTML = ''
  })

  const setupFocusableElement = () => {
    const focusTarget = document.createElement('button')
    document.body.appendChild(focusTarget)
    focusTarget.focus()
    return focusTarget
  }

  it('should initialize without errors', () => {
    const { result } = renderHook(() =>
      useKeyboardShortcuts({
        onZoomIn: mockOnZoomIn,
        onZoomOut: mockOnZoomOut,
        onToggleLayout: mockOnToggleLayout,
        onShowHelp: mockOnShowHelp,
        rootNodeId: 'root-1',
      })
    )

    expect(result.current).toBeUndefined()
  })

  it('should focus search input when "/" is pressed', async () => {
    const mockSearchInput = document.createElement('input')
    mockSearchInput.setAttribute('aria-label', 'Search taxonomy nodes')
    document.body.appendChild(mockSearchInput)

    renderHook(() =>
      useKeyboardShortcuts({
        onZoomIn: mockOnZoomIn,
        onZoomOut: mockOnZoomOut,
        onToggleLayout: mockOnToggleLayout,
        onShowHelp: mockOnShowHelp,
        rootNodeId: 'root-1',
      })
    )

    await user.keyboard('/')

    await waitFor(() => {
      expect(document.activeElement).toBe(mockSearchInput)
    })
  })

  it('should call onZoomIn when "+" is pressed', async () => {
    setupFocusableElement()

    renderHook(() =>
      useKeyboardShortcuts({
        onZoomIn: mockOnZoomIn,
        onZoomOut: mockOnZoomOut,
        onToggleLayout: mockOnToggleLayout,
        onShowHelp: mockOnShowHelp,
        rootNodeId: 'root-1',
      })
    )

    // Simulate Shift+= using KeyboardEvent
    // Note: userEvent.keyboard('{Shift>}={/Shift}') doesn't reliably trigger react-hotkeys-hook
    const event = new KeyboardEvent('keydown', {
      key: '=',
      code: 'Equal',
      shiftKey: true,
      bubbles: true,
      cancelable: true,
    })
    document.dispatchEvent(event)

    await waitFor(() => {
      expect(mockOnZoomIn).toHaveBeenCalled()
    })
  })

  it('should call onZoomIn when "=" is pressed', async () => {
    setupFocusableElement()

    renderHook(() =>
      useKeyboardShortcuts({
        onZoomIn: mockOnZoomIn,
        onZoomOut: mockOnZoomOut,
        onToggleLayout: mockOnToggleLayout,
        onShowHelp: mockOnShowHelp,
        rootNodeId: 'root-1',
      })
    )

    await user.keyboard('=')

    await waitFor(() => {
      expect(mockOnZoomIn).toHaveBeenCalled()
    })
  })

  it('should call onZoomOut when "-" is pressed', async () => {
    setupFocusableElement()

    renderHook(() =>
      useKeyboardShortcuts({
        onZoomIn: mockOnZoomIn,
        onZoomOut: mockOnZoomOut,
        onToggleLayout: mockOnToggleLayout,
        onShowHelp: mockOnShowHelp,
        rootNodeId: 'root-1',
      })
    )

    await user.keyboard('-')

    await waitFor(() => {
      expect(mockOnZoomOut).toHaveBeenCalled()
    })
  })

  it('should call onToggleLayout when "L" is pressed', async () => {
    setupFocusableElement()

    renderHook(() =>
      useKeyboardShortcuts({
        onZoomIn: mockOnZoomIn,
        onZoomOut: mockOnZoomOut,
        onToggleLayout: mockOnToggleLayout,
        onShowHelp: mockOnShowHelp,
        rootNodeId: 'root-1',
      })
    )

    await user.keyboard('l')

    await waitFor(() => {
      expect(mockOnToggleLayout).toHaveBeenCalled()
    })
  })

  it('should focus root node when "Home" is pressed', async () => {
    setupFocusableElement()

    renderHook(() =>
      useKeyboardShortcuts({
        onZoomIn: mockOnZoomIn,
        onZoomOut: mockOnZoomOut,
        onToggleLayout: mockOnToggleLayout,
        onShowHelp: mockOnShowHelp,
        rootNodeId: 'root-1',
      })
    )

    await user.keyboard('{Home}')

    await waitFor(() => {
      expect(mockSetFocus).toHaveBeenCalledWith('root-1')
    })
  })

  it('should call onShowHelp when "?" (Shift+/) is pressed', async () => {
    setupFocusableElement()

    renderHook(() =>
      useKeyboardShortcuts({
        onZoomIn: mockOnZoomIn,
        onZoomOut: mockOnZoomOut,
        onToggleLayout: mockOnToggleLayout,
        onShowHelp: mockOnShowHelp,
        rootNodeId: 'root-1',
      })
    )

    // ? is Shift+/
    await user.keyboard('{Shift>}/{/Shift}')

    await waitFor(() => {
      expect(mockOnShowHelp).toHaveBeenCalled()
    })
  })

  it('should not trigger shortcuts when keyboardMode is "search"', async () => {
    // Mock keyboard mode as search
    vi.mocked(useTaxonomyStore).mockReturnValue('search')

    renderHook(() =>
      useKeyboardShortcuts({
        onZoomIn: mockOnZoomIn,
        onZoomOut: mockOnZoomOut,
        onToggleLayout: mockOnToggleLayout,
        onShowHelp: mockOnShowHelp,
        rootNodeId: 'root-1',
      })
    )

    await user.keyboard('=')

    // Wait a bit to ensure no calls are made
    await new Promise((resolve) => setTimeout(resolve, 100))

    expect(mockOnZoomIn).not.toHaveBeenCalled()
  })

  it('should not trigger shortcuts when keyboardMode is "panel"', async () => {
    // Mock keyboard mode as panel
    vi.mocked(useTaxonomyStore).mockReturnValue('panel')

    renderHook(() =>
      useKeyboardShortcuts({
        onZoomIn: mockOnZoomIn,
        onZoomOut: mockOnZoomOut,
        onToggleLayout: mockOnToggleLayout,
        onShowHelp: mockOnShowHelp,
        rootNodeId: 'root-1',
      })
    )

    await user.keyboard('l')

    // Wait a bit to ensure no calls are made
    await new Promise((resolve) => setTimeout(resolve, 100))

    expect(mockOnToggleLayout).not.toHaveBeenCalled()
  })
})
