// @TEST:TAXONOMY-VIZ-001-014
// TaxonomyLayoutToggle component tests - layout switching button

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TaxonomyLayoutToggle from '../TaxonomyLayoutToggle'

describe('TaxonomyLayoutToggle', () => {
  const mockOnLayoutChange = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render toggle button when in tree layout', () => {
    render(
      <TaxonomyLayoutToggle
        currentLayout="tree"
        onLayoutChange={mockOnLayoutChange}
      />
    )

    const button = screen.getByRole('button', {
      name: /switch to radial layout/i,
    })
    expect(button).toBeInTheDocument()
  })

  it('should show "Switch to Radial Layout" text when in tree mode', () => {
    render(
      <TaxonomyLayoutToggle
        currentLayout="tree"
        onLayoutChange={mockOnLayoutChange}
      />
    )

    expect(screen.getByText(/switch to radial layout/i)).toBeInTheDocument()
  })

  it('should render toggle button when in radial layout', () => {
    render(
      <TaxonomyLayoutToggle
        currentLayout="radial"
        onLayoutChange={mockOnLayoutChange}
      />
    )

    const button = screen.getByRole('button', {
      name: /switch to tree layout/i,
    })
    expect(button).toBeInTheDocument()
  })

  it('should show "Switch to Tree Layout" text when in radial mode', () => {
    render(
      <TaxonomyLayoutToggle
        currentLayout="radial"
        onLayoutChange={mockOnLayoutChange}
      />
    )

    expect(screen.getByText(/switch to tree layout/i)).toBeInTheDocument()
  })

  it('should call onLayoutChange with "radial" when clicked in tree mode', async () => {
    const user = userEvent.setup()
    render(
      <TaxonomyLayoutToggle
        currentLayout="tree"
        onLayoutChange={mockOnLayoutChange}
      />
    )

    const button = screen.getByRole('button', {
      name: /switch to radial layout/i,
    })
    await user.click(button)

    expect(mockOnLayoutChange).toHaveBeenCalledTimes(1)
    expect(mockOnLayoutChange).toHaveBeenCalledWith('radial')
  })

  it('should call onLayoutChange with "tree" when clicked in radial mode', async () => {
    const user = userEvent.setup()
    render(
      <TaxonomyLayoutToggle
        currentLayout="radial"
        onLayoutChange={mockOnLayoutChange}
      />
    )

    const button = screen.getByRole('button', {
      name: /switch to tree layout/i,
    })
    await user.click(button)

    expect(mockOnLayoutChange).toHaveBeenCalledTimes(1)
    expect(mockOnLayoutChange).toHaveBeenCalledWith('tree')
  })

  it('should toggle between layouts on multiple clicks', async () => {
    const user = userEvent.setup()
    const { rerender } = render(
      <TaxonomyLayoutToggle
        currentLayout="tree"
        onLayoutChange={mockOnLayoutChange}
      />
    )

    // First click: tree -> radial
    let button = screen.getByRole('button', {
      name: /switch to radial layout/i,
    })
    await user.click(button)
    expect(mockOnLayoutChange).toHaveBeenCalledWith('radial')

    // Simulate state update
    rerender(
      <TaxonomyLayoutToggle
        currentLayout="radial"
        onLayoutChange={mockOnLayoutChange}
      />
    )

    // Second click: radial -> tree
    button = screen.getByRole('button', {
      name: /switch to tree layout/i,
    })
    await user.click(button)
    expect(mockOnLayoutChange).toHaveBeenCalledWith('tree')
    expect(mockOnLayoutChange).toHaveBeenCalledTimes(2)
  })

  it('should have correct ARIA label for tree layout', () => {
    render(
      <TaxonomyLayoutToggle
        currentLayout="tree"
        onLayoutChange={mockOnLayoutChange}
      />
    )

    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-label', 'Switch to radial layout')
  })

  it('should have correct ARIA label for radial layout', () => {
    render(
      <TaxonomyLayoutToggle
        currentLayout="radial"
        onLayoutChange={mockOnLayoutChange}
      />
    )

    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-label', 'Switch to tree layout')
  })

  it('should display radial icon when in tree mode', () => {
    const { container } = render(
      <TaxonomyLayoutToggle
        currentLayout="tree"
        onLayoutChange={mockOnLayoutChange}
      />
    )

    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
    // Circle icon for radial layout
    const circle = container.querySelector('circle')
    expect(circle).toBeInTheDocument()
  })

  it('should display tree icon when in radial mode', () => {
    const { container } = render(
      <TaxonomyLayoutToggle
        currentLayout="radial"
        onLayoutChange={mockOnLayoutChange}
      />
    )

    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
    // Tree icon has vertical and arrow paths (M12 2v20M...)
    const path = container.querySelector('path')
    expect(path).toBeInTheDocument()
    expect(path).toHaveAttribute('d', expect.stringContaining('M12 2v20'))
  })
})
