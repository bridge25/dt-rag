// @TEST:FRONTEND-INTEGRATION-001:XP-API
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { awardXP } from '../xp'
import * as clientModule from '../client'

vi.mock('../client', () => ({
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
        agent_id: '123',
        current_xp: 1100,
        new_level: 5,
        leveled_up: false,
      }

      vi.mocked(clientModule.apiClient.post).mockResolvedValue(mockResponse)

      const result = await awardXP({
        agentId: '123',
        amount: 100,
        reason: 'chat',
      })

      expect(result).toEqual(mockResponse)
      expect(clientModule.apiClient.post).toHaveBeenCalledWith(
        '/api/v1/agents/123/xp',
        { amount: 100, reason: 'chat' }
      )
    })

    it('should handle level up', async () => {
      const mockResponse = {
        agent_id: '123',
        current_xp: 2100,
        new_level: 6,
        leveled_up: true,
      }

      vi.mocked(clientModule.apiClient.post).mockResolvedValue(mockResponse)

      const result = await awardXP({
        agentId: '123',
        amount: 1000,
        reason: 'ragas_bonus',
      })

      expect(result.leveled_up).toBe(true)
      expect(result.new_level).toBe(6)
    })

    it('should handle different XP reasons', async () => {
      const reasons = ['chat', 'positive_feedback', 'ragas_bonus'] as const

      for (const reason of reasons) {
        vi.mocked(clientModule.apiClient.post).mockResolvedValue({
          agent_id: '123',
          current_xp: 1100,
          new_level: 5,
          leveled_up: false,
        })

        await awardXP({ agentId: '123', amount: 100, reason })

        expect(clientModule.apiClient.post).toHaveBeenCalledWith(
          '/api/v1/agents/123/xp',
          { amount: 100, reason }
        )
      }
    })
  })
})
