/**
 * Test file
 *
 * @CODE:FRONTEND-001
 * @TEST:FRONTEND-001
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fetchCoverageHistory } from '../history'
import * as clientModule from '../client'

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}))

describe('History API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchCoverageHistory', () => {
    it('should fetch coverage history successfully', async () => {
      const mockResponse = {
        agent_id: '123',
        history: [
          { date: '2025-10-01T00:00:00Z', coverage: 75.5, xp: 1200 },
          { date: '2025-10-02T00:00:00Z', coverage: 78.3, xp: 1350 },
        ],
        interval: 'daily' as const,
      }

      vi.mocked(clientModule.apiClient.get).mockResolvedValue(mockResponse)

      const result = await fetchCoverageHistory('123', { interval: 'daily' })

      expect(result).toEqual(mockResponse)
      expect(clientModule.apiClient.get).toHaveBeenCalledWith(
        '/api/v1/agents/123/coverage/history',
        { interval: 'daily' }
      )
    })

    it('should handle date range params', async () => {
      const mockResponse = {
        agent_id: '123',
        history: [],
        interval: 'weekly' as const,
      }

      vi.mocked(clientModule.apiClient.get).mockResolvedValue(mockResponse)

      await fetchCoverageHistory('123', {
        start_date: '2025-10-01',
        end_date: '2025-10-30',
        interval: 'weekly',
      })

      expect(clientModule.apiClient.get).toHaveBeenCalledWith(
        '/api/v1/agents/123/coverage/history',
        {
          start_date: '2025-10-01',
          end_date: '2025-10-30',
          interval: 'weekly',
        }
      )
    })

    it('should handle empty history', async () => {
      const mockResponse = {
        agent_id: '123',
        history: [],
        interval: 'monthly' as const,
      }

      vi.mocked(clientModule.apiClient.get).mockResolvedValue(mockResponse)

      const result = await fetchCoverageHistory('123')

      expect(result.history).toHaveLength(0)
    })
  })
})
