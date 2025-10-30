// @TEST:AGENT-CARD-001-HOOK-001
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAgents } from './useAgents'
import { apiClient } from '@/lib/api/client'
import type { ReactNode } from 'react'

vi.mock('@/lib/api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}))

const mockApiClient = apiClient as { get: ReturnType<typeof vi.fn> }

const mockAgentsData = {
  agents: [
    {
      agent_id: 'agent-1',
      name: 'Test Agent 1',
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
      name: 'Test Agent 2',
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
  ]
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

describe('useAgents', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Successful Data Fetching', () => {
    it('should fetch agents data successfully', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: mockAgentsData,
      })

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.agents).toEqual([])

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.agents).toHaveLength(2)
      expect(result.current.agents[0].name).toBe('Test Agent 1')
      expect(result.current.agents[1].name).toBe('Test Agent 2')
      expect(result.current.error).toBeNull()
    })

    it('should call the correct API endpoint', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: mockAgentsData,
      })

      renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(mockApiClient.get).toHaveBeenCalledWith('/agents')
      })
    })

    it('should return empty array when no agents exist', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: { agents: [] },
      })

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.agents).toEqual([])
      expect(result.current.error).toBeNull()
    })
  })

  describe('Loading States', () => {
    it('should show loading state initially', () => {
      mockApiClient.get.mockImplementation(() => new Promise(() => {}))

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.agents).toEqual([])
    })

    it('should transition from loading to loaded', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: mockAgentsData,
      })

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(true)

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.agents).toHaveLength(2)
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      mockApiClient.get.mockRejectedValueOnce(new Error('Network error'))

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBeTruthy()
      expect(result.current.agents).toEqual([])
    })

    it('should handle HTTP error responses', async () => {
      mockApiClient.get.mockRejectedValueOnce({
        response: {
          status: 500,
          statusText: 'Internal Server Error',
        },
      })

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBeTruthy()
      expect(result.current.agents).toEqual([])
    })

    it('should handle 404 errors', async () => {
      mockApiClient.get.mockRejectedValueOnce({
        response: {
          status: 404,
          statusText: 'Not Found',
        },
      })

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBeTruthy()
    })

    it('should handle malformed JSON response', async () => {
      mockApiClient.get.mockRejectedValueOnce(new Error('Invalid JSON'))

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBeTruthy()
    })
  })

  describe('Refetch Functionality', () => {
    it('should provide refetch function', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: mockAgentsData,
      })

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.refetch).toBeDefined()
      expect(typeof result.current.refetch).toBe('function')
    })

    it('should refetch data when refetch is called', async () => {
      mockApiClient.get
        .mockResolvedValueOnce({
          data: mockAgentsData,
        })
        .mockResolvedValueOnce({
          data: {
            agents: [
              {
                ...mockAgentsData.agents[0],
                level: 4,
              },
            ],
          },
        })

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.agents).toHaveLength(2)

      await result.current.refetch()

      await waitFor(() => {
        expect(result.current.agents).toHaveLength(1)
      })

      expect(result.current.agents[0].level).toBe(4)
    })
  })

  describe('Data Transformation', () => {
    it('should properly type agent data', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: mockAgentsData,
      })

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      const agent = result.current.agents[0]
      expect(agent).toHaveProperty('agent_id')
      expect(agent).toHaveProperty('name')
      expect(agent).toHaveProperty('level')
      expect(agent).toHaveProperty('rarity')
      expect(agent).toHaveProperty('total_documents')
      expect(agent).toHaveProperty('total_queries')
      expect(agent).toHaveProperty('quality_score')
    })

    it('should handle agents with null next_level_xp', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: mockAgentsData,
      })

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      const maxLevelAgent = result.current.agents[1]
      expect(maxLevelAgent.next_level_xp).toBeNull()
    })
  })

  describe('Edge Cases', () => {
    it('should handle undefined last_used field', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: {
          agents: [
            {
              ...mockAgentsData.agents[0],
              last_used: undefined,
            },
          ],
        },
      })

      const { result } = renderHook(() => useAgents(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.agents[0].last_used).toBeUndefined()
    })

    it('should handle all rarity types', async () => {
      const allRarities = ['Common', 'Rare', 'Epic', 'Legendary'] as const

      for (const rarity of allRarities) {
        mockApiClient.get.mockResolvedValueOnce({
          data: {
            agents: [
              {
                ...mockAgentsData.agents[0],
                rarity,
              },
            ],
          },
        })

        const { result } = renderHook(() => useAgents(), {
          wrapper: createWrapper(),
        })

        await waitFor(() => {
          expect(result.current.isLoading).toBe(false)
        })

        expect(result.current.agents[0].rarity).toBe(rarity)
      }
    })
  })
})
