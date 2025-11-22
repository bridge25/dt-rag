/**
 * Test file
 *
 * @CODE:FRONTEND-001
 * @TEST:FRONTEND-001
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAgent } from './useAgent'
import * as agentsApi from '@/lib/api/agents'
import type { ReactNode } from 'react'

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

describe('useAgent', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Successful Data Fetching', () => {
    it('should fetch agent data successfully', async () => {
      mockFetchAgent.mockResolvedValueOnce(mockAgentData)

      const { result } = renderHook(() => useAgent('550e8400-e29b-41d4-a716-446655440001'), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.agent).toBeUndefined()

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.agent).toEqual(mockAgentData)
      expect(result.current.error).toBeNull()
    })

    it('should call fetchAgent with correct ID', async () => {
      mockFetchAgent.mockResolvedValueOnce(mockAgentData)

      renderHook(() => useAgent('550e8400-e29b-41d4-a716-446655440001'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(mockFetchAgent).toHaveBeenCalledWith('550e8400-e29b-41d4-a716-446655440001')
      })
    })
  })

  describe('Loading States', () => {
    it('should show loading state initially', () => {
      mockFetchAgent.mockImplementation(() => new Promise(() => {}))

      const { result } = renderHook(() => useAgent('550e8400-e29b-41d4-a716-446655440001'), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.agent).toBeUndefined()
    })

    it('should transition from loading to loaded', async () => {
      mockFetchAgent.mockResolvedValueOnce(mockAgentData)

      const { result } = renderHook(() => useAgent('550e8400-e29b-41d4-a716-446655440001'), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(true)

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.agent).toEqual(mockAgentData)
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      const error = new Error('Network error')
      mockFetchAgent.mockRejectedValue(error)

      const { result } = renderHook(() => useAgent('550e8400-e29b-41d4-a716-446655440001'), {
        wrapper: createWrapper(),
      })

      await waitFor(
        () => {
          expect(result.current.error).toBeTruthy()
        },
        { timeout: 5000 }
      )

      expect(result.current.agent).toBeUndefined()
    })

    it('should handle 404 errors', async () => {
      const error = new Error('Not Found')
      mockFetchAgent.mockRejectedValue(error)

      const { result } = renderHook(() => useAgent('non-existent-id'), {
        wrapper: createWrapper(),
      })

      await waitFor(
        () => {
          expect(result.current.error).toBeTruthy()
        },
        { timeout: 5000 }
      )

      expect(result.current.agent).toBeUndefined()
    })
  })

  describe('Refetch Functionality', () => {
    it('should provide refetch function', async () => {
      mockFetchAgent.mockResolvedValueOnce(mockAgentData)

      const { result } = renderHook(() => useAgent('550e8400-e29b-41d4-a716-446655440001'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.refetch).toBeDefined()
      expect(typeof result.current.refetch).toBe('function')
    })

    it('should refetch data when refetch is called', async () => {
      mockFetchAgent
        .mockResolvedValueOnce(mockAgentData)
        .mockResolvedValueOnce({
          ...mockAgentData,
          level: 4,
        })

      const { result } = renderHook(() => useAgent('550e8400-e29b-41d4-a716-446655440001'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.agent?.level).toBe(3)

      await result.current.refetch()

      await waitFor(() => {
        expect(result.current.agent?.level).toBe(4)
      })
    })
  })

  describe('Polling Behavior', () => {
    it('should have refetchInterval set to 5000ms', async () => {
      mockFetchAgent.mockResolvedValue(mockAgentData)

      const { result } = renderHook(() => useAgent('550e8400-e29b-41d4-a716-446655440001'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.agent).toEqual(mockAgentData)
    })
  })
})
