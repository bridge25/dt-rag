// @TEST:FRONTEND-INTEGRATION-001:PHASE3:XP-API
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { awardXP } from './xp'
import { apiClient } from './client'

vi.mock('./client', () => ({
  apiClient: {
    post: vi.fn(),
  },
}))

describe('XP API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('awardXP', () => {
    it('should award XP successfully', async () => {
      const mockResponse = {
        agent_id: 'test-agent-id',
        current_xp: 110,
        new_level: 1,
        leveled_up: false,
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const result = await awardXP({
        agentId: 'test-agent-id',
        amount: 10,
        reason: 'chat',
      })

      expect(result).toEqual(mockResponse)
      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/agents/test-agent-id/xp',
        {
          amount: 10,
          reason: 'chat',
        }
      )
    })

    it('should handle 404 error gracefully', async () => {
      const error = { status: 404, message: 'Not Found' }
      vi.mocked(apiClient.post).mockRejectedValue(error)

      const result = await awardXP({
        agentId: 'test-agent-id',
        amount: 50,
        reason: 'positive_feedback',
      })

      expect(result).toEqual({
        agent_id: 'test-agent-id',
        current_xp: 0,
        new_level: 1,
        leveled_up: false,
      })
    })

    it('should throw other errors', async () => {
      const error = new Error('Network error')
      vi.mocked(apiClient.post).mockRejectedValue(error)

      await expect(
        awardXP({
          agentId: 'test-agent-id',
          amount: 100,
          reason: 'ragas_bonus',
        })
      ).rejects.toThrow('Network error')
    })

    it('should award XP with level up', async () => {
      const mockResponse = {
        agent_id: 'test-agent-id',
        current_xp: 500,
        new_level: 2,
        leveled_up: true,
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const result = await awardXP({
        agentId: 'test-agent-id',
        amount: 100,
        reason: 'ragas_bonus',
      })

      expect(result).toEqual(mockResponse)
      expect(result.leveled_up).toBe(true)
    })
  })
})
