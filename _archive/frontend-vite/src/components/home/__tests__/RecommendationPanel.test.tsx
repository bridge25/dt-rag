/**
 * RecommendationPanel Component Tests
 *
 * Tests for the RecommendationPanel component that shows
 * contextual recommendations based on user state.
 *
 * @TEST:HOME-STATS-001
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { RecommendationPanel } from '../RecommendationPanel'

describe('RecommendationPanel', () => {
  describe('when user has no agents', () => {
    it('renders get started message', () => {
      render(<RecommendationPanel hasAgents={false} />)

      expect(screen.getByText('Get Started')).toBeInTheDocument()
    })

    it('shows create agent instruction', () => {
      render(<RecommendationPanel hasAgents={false} />)

      expect(
        screen.getByText(/Create your first agent/i)
      ).toBeInTheDocument()
    })

    it('shows upload documents instruction', () => {
      render(<RecommendationPanel hasAgents={false} />)

      expect(
        screen.getByText(/Upload documents to build your taxonomy/i)
      ).toBeInTheDocument()
    })

    it('renders create agent button when callback provided', () => {
      const mockOnCreate = vi.fn()
      render(
        <RecommendationPanel hasAgents={false} onCreateAgent={mockOnCreate} />
      )

      const button = screen.getByRole('button', {
        name: /Create Your First Agent/i,
      })
      expect(button).toBeInTheDocument()
    })

    it('calls onCreateAgent when button clicked', () => {
      const mockOnCreate = vi.fn()
      render(
        <RecommendationPanel hasAgents={false} onCreateAgent={mockOnCreate} />
      )

      const button = screen.getByRole('button', {
        name: /Create Your First Agent/i,
      })
      fireEvent.click(button)

      expect(mockOnCreate).toHaveBeenCalledTimes(1)
    })

    it('does not render button when callback not provided', () => {
      render(<RecommendationPanel hasAgents={false} />)

      expect(
        screen.queryByRole('button', { name: /Create Your First Agent/i })
      ).not.toBeInTheDocument()
    })

    it('applies blue styling for new users', () => {
      const { container } = render(<RecommendationPanel hasAgents={false} />)

      const panel = container.firstChild as HTMLElement
      expect(panel).toHaveClass('bg-blue-50', 'border-blue-200')
    })
  })

  describe('when user has agents', () => {
    it('renders recommended actions message', () => {
      render(<RecommendationPanel hasAgents={true} />)

      expect(screen.getByText('Recommended Actions')).toBeInTheDocument()
    })

    it('shows upload more documents recommendation', () => {
      render(<RecommendationPanel hasAgents={true} />)

      expect(
        screen.getByText(/Upload more documents/i)
      ).toBeInTheDocument()
    })

    it('shows chat with agents recommendation', () => {
      render(<RecommendationPanel hasAgents={true} />)

      expect(
        screen.getByText(/Chat with your agents/i)
      ).toBeInTheDocument()
    })

    it('shows review taxonomy recommendation', () => {
      render(<RecommendationPanel hasAgents={true} />)

      expect(
        screen.getByText(/Review taxonomy structure/i)
      ).toBeInTheDocument()
    })

    it('applies purple styling for existing users', () => {
      const { container } = render(<RecommendationPanel hasAgents={true} />)

      const panel = container.firstChild as HTMLElement
      expect(panel).toHaveClass('bg-purple-50', 'border-purple-200')
    })

    it('does not render create agent button', () => {
      const mockOnCreate = vi.fn()
      render(
        <RecommendationPanel hasAgents={true} onCreateAgent={mockOnCreate} />
      )

      expect(
        screen.queryByRole('button', { name: /Create Your First Agent/i })
      ).not.toBeInTheDocument()
    })
  })
})
