/**
 * Agent History Page tests
 *
 * @CODE:FRONTEND-001
 * @TEST:FRONTEND-INTEGRATION-001:PHASE2:HISTORY-PAGE
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AgentHistoryPage from './AgentHistoryPage'
import * as agentsApi from '@/lib/api/agents'
import * as historyApi from '@/lib/api/history'

vi.mock('@/lib/api/agents', () => ({
  fetchAgent: vi.fn(),
}))

vi.mock('@/lib/api/history', () => ({
  fetchCoverageHistory: vi.fn(),
}))

const mockFetchAgent = agentsApi.fetchAgent as ReturnType<typeof vi.fn>
const mockFetchCoverageHistory = historyApi.fetchCoverageHistory as ReturnType<typeof vi.fn>

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

const mockHistoryData = {
  agent_id: '550e8400-e29b-41d4-a716-446655440001',
  history: [
    { date: '2025-01-01', coverage: 50, xp: 100 },
    { date: '2025-01-02', coverage: 55, xp: 120 },
    { date: '2025-01-03', coverage: 60, xp: 150 },
  ],
  interval: 'daily' as const,
}

function renderWithRouter(initialRoute = '/agents/550e8400-e29b-41d4-a716-446655440001/history') {
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
          <Route path="/agents/:id/history" element={<AgentHistoryPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('AgentHistoryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Loading State', () => {
    it('should show loading state initially', () => {
      mockFetchAgent.mockImplementation(() => new Promise(() => {}))
      mockFetchCoverageHistory.mockImplementation(() => new Promise(() => {}))
      renderWithRouter()

      const loadingElements = screen.getAllByRole('generic')
      expect(loadingElements.length).toBeGreaterThan(0)
    })
  })

  describe('Success State', () => {
    it('should render page header with agent name', async () => {
      mockFetchAgent.mockResolvedValueOnce(mockAgentData)
      mockFetchCoverageHistory.mockResolvedValueOnce(mockHistoryData)
      renderWithRouter()

      await waitFor(() => {
        expect(screen.getByText(/Test Agent - History & Analytics/i)).toBeInTheDocument()
      })
    })

    it('should display agent level and rarity', async () => {
      mockFetchAgent.mockResolvedValueOnce(mockAgentData)
      mockFetchCoverageHistory.mockResolvedValueOnce(mockHistoryData)
      renderWithRouter()

      await waitFor(() => {
        expect(screen.getByText(/Level 3/i)).toBeInTheDocument()
      })

      expect(screen.getByText(/Rare/i)).toBeInTheDocument()
    })

    it('should show chart placeholders', async () => {
      mockFetchAgent.mockResolvedValueOnce(mockAgentData)
      mockFetchCoverageHistory.mockResolvedValueOnce(mockHistoryData)
      renderWithRouter()

      await waitFor(() => {
        expect(screen.getByText('Coverage Trend')).toBeInTheDocument()
      })

      expect(screen.getByText('XP Growth')).toBeInTheDocument()
    })

    it('should display summary statistics', async () => {
      mockFetchAgent.mockResolvedValueOnce(mockAgentData)
      mockFetchCoverageHistory.mockResolvedValueOnce(mockHistoryData)
      renderWithRouter()

      await waitFor(() => {
        expect(screen.getByText('Summary Statistics')).toBeInTheDocument()
      })

      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText('50')).toBeInTheDocument()
      expect(screen.getByText('85')).toBeInTheDocument()
    })

    it('should render navigation links', async () => {
      mockFetchAgent.mockResolvedValueOnce(mockAgentData)
      mockFetchCoverageHistory.mockResolvedValueOnce(mockHistoryData)
      renderWithRouter()

      await waitFor(() => {
        expect(screen.getByText('View Details')).toBeInTheDocument()
      })

      expect(screen.getByText(/Back/i)).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should show error message on fetch failure', async () => {
      mockFetchAgent.mockRejectedValue(new Error('Network error'))
      mockFetchCoverageHistory.mockResolvedValueOnce(mockHistoryData)
      renderWithRouter()

      await waitFor(() => {
        expect(screen.getByText(/Error:/i)).toBeInTheDocument()
      }, { timeout: 10000 })

      expect(screen.getByText(/Failed to load agent history/i)).toBeInTheDocument()
    })
  })
})
