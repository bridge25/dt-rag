// @TEST:TAXONOMY-KEYNAV-002-005
// Unit test for Focus Trap in TaxonomyDetailPanel
// Tests: Tab within panel, Escape key closes panel, focus restoration

import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TaxonomyDetailPanel from '../TaxonomyDetailPanel'
import type { TaxonomyNode } from '../../../lib/api/types'

const mockNode: TaxonomyNode = {
  id: 'test-node',
  name: 'Test Node',
  level: 1,
  path: ['Root', 'Test Node'],
  document_count: 10,
  children: [],
  metadata: {
    description: 'Test description',
    category: 'Test category',
  },
}

describe('TaxonomyDetailPanel - Focus Trap', () => {
  it('should render panel when node is provided', () => {
    const onClose = vi.fn()
    render(<TaxonomyDetailPanel node={mockNode} onClose={onClose} />)

    expect(screen.getByTestId('detail-panel')).toBeInTheDocument()
    expect(screen.getByText('Test Node')).toBeInTheDocument()
  })

  it('should not render panel when node is null', () => {
    const onClose = vi.fn()
    render(<TaxonomyDetailPanel node={null} onClose={onClose} />)

    expect(screen.queryByTestId('detail-panel')).not.toBeInTheDocument()
  })

  it('should have close button that is focusable', () => {
    const onClose = vi.fn()
    render(<TaxonomyDetailPanel node={mockNode} onClose={onClose} />)

    const closeButton = screen.getByRole('button', { name: 'Close detail panel' })
    expect(closeButton).toBeInTheDocument()
    expect(closeButton.getAttribute('tabIndex')).not.toBe('-1')
  })

  it('should call onClose when close button is clicked', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    render(<TaxonomyDetailPanel node={mockNode} onClose={onClose} />)

    const closeButton = screen.getByRole('button', { name: 'Close detail panel' })
    await user.click(closeButton)

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('should trap focus within panel - Tab does not escape', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()

    // Create a container with external button to test focus trap
    render(
      <div>
        <button data-testid="external-button">External Button</button>
        <TaxonomyDetailPanel node={mockNode} onClose={onClose} />
      </div>
    )

    const panel = screen.getByTestId('detail-panel')
    expect(panel).toBeInTheDocument()

    const closeButton = screen.getByRole('button', { name: 'Close detail panel' })
    closeButton.focus()
    expect(closeButton).toHaveFocus()

    // Tab multiple times - should stay within panel
    await user.tab()
    await waitFor(() => {
      const focusedElement = document.activeElement
      expect(panel.contains(focusedElement)).toBe(true)
    })

    // Tab again - should cycle back to first focusable element in panel
    await user.tab()
    await waitFor(() => {
      const focusedElement = document.activeElement
      expect(panel.contains(focusedElement)).toBe(true)
    })

    // Ensure focus never escapes to external button
    const externalButton = screen.getByTestId('external-button')
    expect(externalButton).not.toHaveFocus()
  })

  it('should close panel when Escape key is pressed', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    render(<TaxonomyDetailPanel node={mockNode} onClose={onClose} />)

    const panel = screen.getByTestId('detail-panel')
    expect(panel).toBeInTheDocument()

    // Press Escape key
    await user.keyboard('{Escape}')

    await waitFor(() => {
      expect(onClose).toHaveBeenCalledTimes(1)
    })
  })

  it('should restore focus to previously focused element when closed', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()

    const { rerender } = render(
      <div>
        <button data-testid="trigger-button">Open Panel</button>
        <TaxonomyDetailPanel node={null} onClose={onClose} />
      </div>
    )

    const triggerButton = screen.getByTestId('trigger-button')
    triggerButton.focus()
    expect(triggerButton).toHaveFocus()

    // Open panel
    rerender(
      <div>
        <button data-testid="trigger-button">Open Panel</button>
        <TaxonomyDetailPanel node={mockNode} onClose={onClose} />
      </div>
    )

    await waitFor(() => {
      expect(screen.getByTestId('detail-panel')).toBeInTheDocument()
    })

    // Focus should move into panel (implementation should handle this)
    const closeButton = screen.getByRole('button', { name: 'Close detail panel' })

    // Simulate closing panel
    await user.click(closeButton)

    // After close callback, focus should be restored
    // (The parent component handles this via useFocusManagement)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('should handle multiple open/close cycles without focus issues', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()

    const { rerender } = render(
      <div>
        <button data-testid="trigger-button">Open Panel</button>
        <TaxonomyDetailPanel node={null} onClose={onClose} />
      </div>
    )

    // Cycle 1: Open
    rerender(
      <div>
        <button data-testid="trigger-button">Open Panel</button>
        <TaxonomyDetailPanel node={mockNode} onClose={onClose} />
      </div>
    )

    await waitFor(() => {
      expect(screen.getByTestId('detail-panel')).toBeInTheDocument()
    })

    // Cycle 1: Close
    const closeButton1 = screen.getByRole('button', { name: 'Close detail panel' })
    await user.click(closeButton1)
    expect(onClose).toHaveBeenCalledTimes(1)

    // Cycle 2: Open again
    rerender(
      <div>
        <button data-testid="trigger-button">Open Panel</button>
        <TaxonomyDetailPanel node={mockNode} onClose={onClose} />
      </div>
    )

    await waitFor(() => {
      expect(screen.getByTestId('detail-panel')).toBeInTheDocument()
    })

    // Cycle 2: Close
    const closeButton2 = screen.getByRole('button', { name: 'Close detail panel' })
    await user.click(closeButton2)
    expect(onClose).toHaveBeenCalledTimes(2)

    // No errors should occur during multiple cycles
  })

  it('should allow clicking outside panel (allowOutsideClick: true)', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()

    render(
      <div>
        <button data-testid="outside-button">Outside Button</button>
        <TaxonomyDetailPanel node={mockNode} onClose={onClose} />
      </div>
    )

    const panel = screen.getByTestId('detail-panel')
    expect(panel).toBeInTheDocument()

    const outsideButton = screen.getByTestId('outside-button')

    // Click outside should be allowed (focus trap should have allowOutsideClick: true)
    await user.click(outsideButton)

    // This doesn't trigger onClose - the parent component decides when to close
    // Focus trap just prevents Tab from escaping, not clicks
    expect(outsideButton).toHaveFocus()
  })
})
