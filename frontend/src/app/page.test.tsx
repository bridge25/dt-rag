// @TEST:AGENT-CARD-001-PAGE-001
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import HomePage from './page'
import type { ReactNode } from 'react'

vi.mock('../hooks/useAgents', () => ({
  useAgents: vi.fn(),
}))

const { useAgents } = await import('../hooks/useAgents')

const mockAgents = [
  {
    agent_id: 'agent-1',
    name: 'Agent Alpha',
    level: 3,
    current_xp: 150,
    next_level_xp: 300,
    rarity: 'Rare' as const,
    total_documents: 100,
    total_queries: 50,
    quality_score: 85,
    status: 'active',
    created_at: '2025-01-01T00:00:00Z',
    last_used: '2025-01-15T00:00:00Z',
  },
  {
    agent_id: 'agent-2',
    name: 'Agent Beta',
    level: 5,
    current_xp: 500,
    next_level_xp: null,
    rarity: 'Epic' as const,
    total_documents: 200,
    total_queries: 100,
    quality_score: 92,
    status: 'active',
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    agent_id: 'agent-3',
    name: 'Agent Gamma',
    level: 8,
    current_xp: 800,
    next_level_xp: 1000,
    rarity: 'Legendary' as const,
    total_documents: 500,
    total_queries: 300,
    quality_score: 98,
    status: 'active',
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    agent_id: 'agent-4',
    name: 'Agent Delta',
    level: 2,
    current_xp: 80,
    next_level_xp: 150,
    rarity: 'Common' as const,
    total_documents: 50,
    total_queries: 20,
    quality_score: 70,
    status: 'active',
    created_at: '2025-01-01T00:00:00Z',
  },
]

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Grid Layout', () => {
    it('should render responsive grid container', () => {
      vi.mocked(useAgents).mockReturnValue({
        agents: mockAgents,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      const { container } = render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      const grid = container.querySelector('[class*="grid"]')
      expect(grid).toBeInTheDocument()
    })

    it('should apply responsive grid classes', () => {
      vi.mocked(useAgents).mockReturnValue({
        agents: mockAgents,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      const { container } = render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      const grid = container.querySelector('[class*="grid"]')
      expect(grid?.className).toMatch(/grid-cols-1/)
      expect(grid?.className).toMatch(/md:grid-cols-2/)
      expect(grid?.className).toMatch(/lg:grid-cols-3/)
      expect(grid?.className).toMatch(/xl:grid-cols-4/)
    })

    it('should render all agent cards in grid', () => {
      vi.mocked(useAgents).mockReturnValue({
        agents: mockAgents,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText('Agent Alpha')).toBeInTheDocument()
      expect(screen.getByText('Agent Beta')).toBeInTheDocument()
      expect(screen.getByText('Agent Gamma')).toBeInTheDocument()
      expect(screen.getByText('Agent Delta')).toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    it('should show loading skeleton when isLoading is true', () => {
      vi.mocked(useAgents).mockReturnValue({
        agents: [],
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      })

      render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText(/loading/i)).toBeInTheDocument()
    })

    it('should not show agent cards while loading', () => {
      vi.mocked(useAgents).mockReturnValue({
        agents: [],
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      })

      render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      expect(screen.queryByText('Agent Alpha')).not.toBeInTheDocument()
    })

    it('should show skeleton cards during loading', () => {
      vi.mocked(useAgents).mockReturnValue({
        agents: [],
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      })

      const { container } = render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      const skeletons = container.querySelectorAll('[class*="animate-pulse"]')
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })

  describe('Empty State', () => {
    it('should show empty state when no agents exist', () => {
      vi.mocked(useAgents).mockReturnValue({
        agents: [],
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText(/no agents/i)).toBeInTheDocument()
    })

    it('should not show grid when empty', () => {
      vi.mocked(useAgents).mockReturnValue({
        agents: [],
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      expect(screen.queryByText('Agent Alpha')).not.toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should show error message when error exists', () => {
      vi.mocked(useAgents).mockReturnValue({
        agents: [],
        isLoading: false,
        error: new Error('Failed to fetch agents'),
        refetch: vi.fn(),
      })

      render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText(/error:/i)).toBeInTheDocument()
      const errorMessages = screen.getAllByText(/failed to fetch/i)
      expect(errorMessages.length).toBeGreaterThan(0)
    })

    it('should provide retry button on error', () => {
      const refetch = vi.fn()
      vi.mocked(useAgents).mockReturnValue({
        agents: [],
        isLoading: false,
        error: new Error('Network error'),
        refetch,
      })

      render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      const retryButton = screen.getByRole('button', { name: /retry/i })
      expect(retryButton).toBeInTheDocument()
    })

    it('should call refetch when retry button clicked', async () => {
      const refetch = vi.fn().mockResolvedValue({})
      vi.mocked(useAgents).mockReturnValue({
        agents: [],
        isLoading: false,
        error: new Error('Network error'),
        refetch,
      })

      render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      const retryButton = screen.getByRole('button', { name: /retry/i })
      retryButton.click()

      await waitFor(() => {
        expect(refetch).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe('Agent Card Interactions', () => {
    it('should handle view action', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

      vi.mocked(useAgents).mockReturnValue({
        agents: [mockAgents[0]],
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      const viewButton = screen.getByRole('button', { name: /view/i })
      viewButton.click()

      expect(consoleSpy).toHaveBeenCalledWith('View agent:', 'agent-1')
      consoleSpy.mockRestore()
    })

    it('should handle delete action', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

      vi.mocked(useAgents).mockReturnValue({
        agents: [mockAgents[0]],
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      const deleteButton = screen.getByRole('button', { name: /delete/i })
      deleteButton.click()

      expect(consoleSpy).toHaveBeenCalledWith('Delete agent:', 'agent-1')
      consoleSpy.mockRestore()
    })
  })

  describe('Page Layout', () => {
    it('should render page title', () => {
      vi.mocked(useAgents).mockReturnValue({
        agents: mockAgents,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByRole('heading', { name: /agents/i })).toBeInTheDocument()
    })

    it('should have proper page container padding', () => {
      vi.mocked(useAgents).mockReturnValue({
        agents: mockAgents,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      const { container } = render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      const mainContainer = container.querySelector('main')
      expect(mainContainer).toHaveClass('p-8')
    })
  })

  describe('Responsive Behavior', () => {
    it('should handle single agent correctly', () => {
      vi.mocked(useAgents).mockReturnValue({
        agents: [mockAgents[0]],
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText('Agent Alpha')).toBeInTheDocument()
      expect(screen.queryByText('Agent Beta')).not.toBeInTheDocument()
    })

    it('should handle many agents correctly', () => {
      const manyAgents = Array.from({ length: 12 }, (_, i) => ({
        ...mockAgents[0],
        agent_id: `agent-${i}`,
        name: `Agent ${i}`,
      }))

      vi.mocked(useAgents).mockReturnValue({
        agents: manyAgents,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      render(
        <HomePage />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText('Agent 0')).toBeInTheDocument()
      expect(screen.getByText('Agent 11')).toBeInTheDocument()
    })
  })
})
