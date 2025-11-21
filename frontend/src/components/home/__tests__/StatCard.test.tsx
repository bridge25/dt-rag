/**
 * StatCard Component Tests
 *
 * Tests for the StatCard component that displays statistics
 * on the home dashboard.
 *
 * @TEST:HOME-STATS-001
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatCard } from '../StatCard'

describe('StatCard', () => {
  const mockIcon = <span data-testid="mock-icon">Icon</span>

  it('renders title and value correctly', () => {
    render(
      <StatCard
        title="Total Agents"
        value={42}
        icon={mockIcon}
      />
    )

    expect(screen.getByText('Total Agents')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('renders string value', () => {
    render(
      <StatCard
        title="Status"
        value="Active"
        icon={mockIcon}
      />
    )

    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('renders icon', () => {
    render(
      <StatCard
        title="Test"
        value={0}
        icon={mockIcon}
      />
    )

    expect(screen.getByTestId('mock-icon')).toBeInTheDocument()
  })

  it('renders description when provided', () => {
    render(
      <StatCard
        title="Documents"
        value={100}
        icon={mockIcon}
        description="Last updated 5 min ago"
      />
    )

    expect(screen.getByText('Last updated 5 min ago')).toBeInTheDocument()
  })

  it('does not render description when not provided', () => {
    render(
      <StatCard
        title="Documents"
        value={100}
        icon={mockIcon}
      />
    )

    // Description paragraph should not exist
    const container = screen.getByText('Documents').closest('div')?.parentElement
    const descriptionElements = container?.querySelectorAll('p.text-xs')
    expect(descriptionElements?.length ?? 0).toBe(0)
  })

  it('applies correct styling classes', () => {
    const { container } = render(
      <StatCard
        title="Test"
        value={0}
        icon={mockIcon}
      />
    )

    const card = container.firstChild as HTMLElement
    expect(card).toHaveClass('bg-white', 'rounded-lg', 'border', 'p-6', 'shadow-sm')
  })
})
