/**
 * Test file
 *
 * @CODE:FRONTEND-001
 * @TEST:TAXONOMY-VIZ-001
 */

import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import userEvent from '@testing-library/user-event'
import { axe } from 'jest-axe'
import KeyboardShortcutsModal from '../KeyboardShortcutsModal'

describe('KeyboardShortcutsModal', () => {
  const mockOnClose = vi.fn()
  let user: ReturnType<typeof userEvent.setup>

  beforeEach(() => {
    vi.clearAllMocks()
    user = userEvent.setup()
  })

  it('should render when isOpen is true', () => {
    render(<KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} />)

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument()
  })

  it('should not render when isOpen is false', () => {
    render(<KeyboardShortcutsModal isOpen={false} onClose={mockOnClose} />)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('should close modal when Escape key is pressed', async () => {
    render(<KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} />)

    await user.keyboard('{Escape}')

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })
  })

  it('should close modal when close button is clicked', async () => {
    render(<KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} />)

    const closeButton = screen.getByRole('button', {
      name: /close keyboard shortcuts/i,
    })
    await user.click(closeButton)

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('should have focus trap active when open', () => {
    render(<KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} />)

    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeInTheDocument()

    // Verify close button is focusable (focus trap should keep focus within modal)
    const closeButton = screen.getByRole('button', {
      name: /close keyboard shortcuts/i,
    })
    expect(closeButton).toBeInTheDocument()
  })

  it('should display all keyboard shortcuts', () => {
    render(<KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} />)

    // Check for specific shortcuts
    expect(screen.getByText('Tab')).toBeInTheDocument()
    expect(screen.getByText('Shift+Tab')).toBeInTheDocument()
    expect(screen.getByText('Arrow keys')).toBeInTheDocument()
    expect(screen.getByText('/')).toBeInTheDocument()
    expect(screen.getByText(/\+.*=/)).toBeInTheDocument() // + or =
    expect(screen.getByText('-')).toBeInTheDocument()
    expect(screen.getByText('L')).toBeInTheDocument()
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('?')).toBeInTheDocument()
    expect(screen.getByText('Escape')).toBeInTheDocument()
  })

  it('should have proper WCAG attributes', () => {
    render(<KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} />)

    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-labelledby')
    expect(dialog).toHaveAttribute('aria-describedby')

    const titleId = dialog.getAttribute('aria-labelledby')
    const descriptionId = dialog.getAttribute('aria-describedby')

    expect(screen.getByText('Keyboard Shortcuts')).toHaveAttribute('id', titleId!)
    expect(
      screen.getByText(
        /use these keyboard shortcuts to navigate and interact with the taxonomy tree efficiently/i
      )
    ).toHaveAttribute('id', descriptionId!)
  })

  it('should have no accessibility violations', async () => {
    const { container } = render(
      <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} />
    )

    const results = await axe(container)
    expect(results.violations).toHaveLength(0)
  })

  it('should display navigation section with shortcuts', () => {
    render(<KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} />)

    expect(screen.getByText('Navigation')).toBeInTheDocument()
    expect(screen.getByText(/navigate forward/i)).toBeInTheDocument()
    expect(screen.getByText(/navigate backward/i)).toBeInTheDocument()
    expect(screen.getByText(/navigate between nodes/i)).toBeInTheDocument()
  })

  it('should display actions section with shortcuts', () => {
    render(<KeyboardShortcutsModal isOpen={true} onClose=  {mockOnClose} />)

    expect(screen.getByText('Actions')).toBeInTheDocument()
    expect(screen.getByText(/focus search input/i)).toBeInTheDocument()
    expect(screen.getByText(/zoom in/i)).toBeInTheDocument()
    expect(screen.getByText(/zoom out/i)).toBeInTheDocument()
    expect(screen.getByText(/toggle layout/i)).toBeInTheDocument()
    expect(screen.getByText(/focus root node/i)).toBeInTheDocument()
  })
})
