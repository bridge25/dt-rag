/**
 * API client for agent XP endpoints
 *
 * @CODE:FRONTEND-MIGRATION-002
 */
import { apiClient } from "./client"
import { AwardXPResponseSchema, type AwardXPResponseType } from "./types"
import { isAxiosError } from "axios"

export interface AwardXPRequest {
  agentId: string
  amount: number
  reason: "chat" | "positive_feedback" | "ragas_bonus"
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
      `/agents/${request.agentId}/xp`,
      {
        amount: request.amount,
        reason: request.reason,
      }
    )

    const validated = AwardXPResponseSchema.parse(response.data)
    return validated
  } catch (error) {
    // Handle 404 gracefully - agent doesn't exist yet
    if (isAxiosError(error) && error.response?.status === 404) {
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
