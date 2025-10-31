// @TEST:FRONTEND-INTEGRATION-001:PHASE2:DETAIL-PAGE
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AgentDetailPage from './AgentDetailPage'
import * as agentsApi from '@/lib/api/agents'

vi.mock('@/lib/api/agents', () => ({
  fetchAgent: vi.fn(),
}))

const mockFetchAgent = agentsApi.fetchAgent as ReturnType<typeof vi.fn>

const mockAgentData = {
  agent_id: '550e8400-e29b-41d4-a716-446655440001',
  name: 'Test Agent',
  level: 3,
  current_xp: 150,
  next_level_xp: 300,
  rarity: 'Rare' as const,
  total_documents: 100,
  total_queries: 50,
  quality_score: 85,
  status: 'active',
  created_at: '2025-01-01T00:00:00.000Z',
  last_used: '2025-01-15T00:00:00.000Z',
}

function renderWithRouter(initialRoute = '/agents/550e8400-e29b-41d4-a716-446655440001') {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        refetchInterval: false,
        refetchOnWindowFocus: false,
        refetchOnMount: false,
        refetchOnReconnect: false,
        staleTime: 0,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path="/agents/:id" element={<AgentDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('AgentDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Loading State', () => {
    it('should show loading state initially', () => {
      mockFetchAgent.mockImplementation(() => new Promise(() => {}))
      const { container } = renderWithRouter()

      const skeletons = container.querySelectorAll('[class*="animate-pulse"]')
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })

  describe('Success State', () => {
    it('should render agent details when data loads successfully', async () => {
      mockFetchAgent.mockResolvedValueOnce(mockAgentData)
      renderWithRouter()

      await waitFor(() => {
        expect(screen.getByText('Test Agent')).toBeInTheDocument()
      })

      expect(screen.getByText('Level 3')).toBeInTheDocument()
      expect(screen.getByText('150 / 300 XP')).toBeInTheDocument()
    })

    it('should display agent stats correctly', async () => {
      mockFetchAgent.mockResolvedValueOnce(mockAgentData)
      renderWithRouter()

      await waitFor(() => {
        expect(screen.getByText('Test Agent')).toBeInTheDocument()
      })

      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText('50')).toBeInTheDocument()
      expect(screen.getByText('85')).toBeInTheDocument()
    })

    it('should display agent metadata', async () => {
      mockFetchAgent.mockResolvedValueOnce(mockAgentData)
      renderWithRouter()

      await waitFor(() => {
        expect(screen.getByText('Test Agent')).toBeInTheDocument()
      })

      expect(screen.getByText(/Agent ID:/i)).toBeInTheDocument()
      expect(screen.getByText(/Status:/i)).toBeInTheDocument()
      expect(screen.getByText(/Created At:/i)).toBeInTheDocument()
    })

    it('should render View History link', async () => {
      mockFetchAgent.mockResolvedValueOnce(mockAgentData)
      renderWithRouter()

      await waitFor(() => {
        expect(screen.getByText('View History')).toBeInTheDocument()
      })
    })
  })

  describe('Error State', () => {
    it('should show error message on fetch failure', async () => {
      mockFetchAgent.mockRejectedValue(new Error('Network error'))
      renderWithRouter()

      await waitFor(() => {
        expect(screen.getByText(/Error:/i)).toBeInTheDocument()
      }, { timeout: 10000 })

      expect(screen.getByText(/Failed to load agent details/i)).toBeInTheDocument()
    })

    it('should show retry button on error', async () => {
      mockFetchAgent.mockRejectedValue(new Error('Network error'))
      renderWithRouter()

      await waitFor(() => {
        expect(screen.getByText('Retry')).toBeInTheDocument()
      }, { timeout: 10000 })
    })
  })

  describe('Navigation', () => {
    it('should render back button', async () => {
      mockFetchAgent.mockResolvedValueOnce(mockAgentData)
      renderWithRouter()

      await waitFor(() => {
        expect(screen.getAllByText(/Back/i)[0]).toBeInTheDocument()
      })
    })
  })
})
