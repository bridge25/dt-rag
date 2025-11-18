// @CODE:FRONTEND-INTEGRATION-001:XP-API
import { apiClient } from './client'
import { AwardXPResponseSchema, type AwardXPResponseType } from './types'

export interface AwardXPRequest {
  agentId: string
  amount: number
  reason: 'chat' | 'positive_feedback' | 'ragas_bonus'
}

export interface AwardXPResponse {
  agent_id: string
  current_xp: number
  new_level: number
  leveled_up: boolean
}

export async function awardXP(request: AwardXPRequest): Promise<AwardXPResponse> {
  try {
    const response = await apiClient.post<AwardXPResponseType>(
      `/api/v1/agents/${request.agentId}/xp`,
      {
        amount: request.amount,
        reason: request.reason,
      }
    )

    const validated = AwardXPResponseSchema.parse(response)
    return validated
  } catch (error) {
    if (error && typeof error === 'object' && 'status' in error && error.status === 404) {
      return {
        agent_id: request.agentId,
        current_xp: 0,
        new_level: 1,
        leveled_up: false,
      }
    }
    throw error
  }
}
