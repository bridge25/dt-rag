// @TEST:FRONTEND-INTEGRATION-001:AGENTS-API
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fetchAgents, fetchAgent, calculateCoverage } from '../agents'
import * as clientModule from '../client'

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}))

describe('Agents API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchAgents', () => {
    it('should fetch agents list successfully', async () => {
      const mockResponse = {
        agents: [
          {
            agent_id: '550e8400-e29b-41d4-a716-446655440000',
            name: 'Test Agent',
            level: 5,
            current_xp: 1000,
            next_level_xp: 2000,
            rarity: 'Rare',
            total_documents: 100,
            total_queries: 50,
            quality_score: 85,
            status: 'active',
            created_at: '2025-10-30T00:00:00Z',
          },
        ],
        total: 1,
        active: 1,
        inactive: 0,
      }

      vi.mocked(clientModule.apiClient.get).mockResolvedValue(mockResponse)

      const result = await fetchAgents({ level: 5 })

      expect(result).toEqual(mockResponse.agents)
      expect(clientModule.apiClient.get).toHaveBeenCalledWith('/api/v1/agents', { level: 5 })
    })

    it('should handle empty params', async () => {
      const mockResponse = { agents: [], total: 0, active: 0, inactive: 0 }
      vi.mocked(clientModule.apiClient.get).mockResolvedValue(mockResponse)

      const result = await fetchAgents()

      expect(result).toEqual([])
      expect(clientModule.apiClient.get).toHaveBeenCalledWith('/api/v1/agents', undefined)
    })
  })

  describe('fetchAgent', () => {
    it('should fetch single agent successfully', async () => {
      const mockAgent = {
        agent_id: '550e8400-e29b-41d4-a716-446655440001',
        name: 'Test Agent',
        level: 5,
        current_xp: 1000,
        next_level_xp: 2000,
        rarity: 'Rare' as const,
        total_documents: 100,
        total_queries: 50,
        quality_score: 85,
        status: 'active',
        created_at: '2025-10-30T00:00:00Z',
      }

      vi.mocked(clientModule.apiClient.get).mockResolvedValue(mockAgent)

      const result = await fetchAgent('550e8400-e29b-41d4-a716-446655440001')

      expect(result).toEqual(mockAgent)
      expect(clientModule.apiClient.get).toHaveBeenCalledWith('/api/v1/agents/550e8400-e29b-41d4-a716-446655440001')
    })
  })

  describe('calculateCoverage', () => {
    it('should fetch coverage successfully', async () => {
      const mockCoverage = {
        agent_id: '550e8400-e29b-41d4-a716-446655440002',
        coverage_percentage: 75.5,
        total_documents: 100,
        covered_documents: 75,
        taxonomy_depth: 3,
      }

      vi.mocked(clientModule.apiClient.get).mockResolvedValue(mockCoverage)

      const result = await calculateCoverage('550e8400-e29b-41d4-a716-446655440002')

      expect(result).toEqual(mockCoverage)
      expect(clientModule.apiClient.get).toHaveBeenCalledWith('/api/v1/agents/550e8400-e29b-41d4-a716-446655440002/coverage')
    })
  })
})
