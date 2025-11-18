// @CODE:FRONTEND-INTEGRATION-001:HISTORY-API
import { apiClient } from './client'
import { z } from 'zod'

export interface CoverageHistoryItem {
  date: string
  coverage: number
  xp: number
}

export interface CoverageHistoryResponse {
  agent_id: string
  history: CoverageHistoryItem[]
  interval: 'daily' | 'weekly' | 'monthly'
}

const CoverageHistoryItemSchema = z.object({
  date: z.string(),
  coverage: z.number(),
  xp: z.number(),
})

const CoverageHistoryResponseSchema = z.object({
  agent_id: z.string(),
  history: z.array(CoverageHistoryItemSchema),
  interval: z.enum(['daily', 'weekly', 'monthly']),
})

export async function fetchCoverageHistory(
  agentId: string,
  params?: {
    start_date?: string
    end_date?: string
    interval?: 'daily' | 'weekly' | 'monthly'
  }
): Promise<CoverageHistoryResponse> {
  try {
    const response = await apiClient.get<CoverageHistoryResponse>(
      `/api/v1/agents/${agentId}/coverage/history`,
      params
    )
    return CoverageHistoryResponseSchema.parse(response)
  } catch (error) {
    if (error && typeof error === 'object' && 'status' in error && error.status === 404) {
      const dummyHistory: CoverageHistoryItem[] = Array.from({ length: 30 }, (_, i) => {
        const date = new Date()
        date.setDate(date.getDate() - (29 - i))
        return {
          date: date.toISOString(),
          coverage: 70 + Math.random() * 20,
          xp: 1000 + i * 50 + Math.floor(Math.random() * 100),
        }
      })

      return {
        agent_id: agentId,
        history: dummyHistory,
        interval: params?.interval || 'daily',
      }
    }
    throw error
  }
}
