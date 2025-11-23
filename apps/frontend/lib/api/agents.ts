/**
 * API client for agent-related endpoints
 *
 * @CODE:FRONTEND-MIGRATION-002
 */
import { apiClient } from "./client"
import {
  AgentCardDataSchema,
  CoverageResponseSchema,
  type AgentCardData,
  type CoverageResponse,
} from "./types"
import { z } from "zod"

const AgentsListResponseSchema = z.object({
  agents: z.array(AgentCardDataSchema),
})

export interface FetchAgentsParams {
  level?: number
  min_coverage?: number
  max_results?: number
  [key: string]: unknown
}

export interface AgentsListResponse {
  agents: AgentCardData[]
}

export async function fetchAgents(
  params?: FetchAgentsParams
): Promise<AgentCardData[]> {
  const response = await apiClient.get<AgentsListResponse>(
    "/agents",
    params ? { params } : undefined
  )
  const validated = AgentsListResponseSchema.parse(response.data)
  return validated.agents
}

export async function fetchAgent(agentId: string): Promise<AgentCardData> {
  const response = await apiClient.get<AgentCardData>(
    `/agents/${agentId}`
  )
  const validated = AgentCardDataSchema.parse(response.data)
  return validated
}

export async function calculateCoverage(
  agentId: string
): Promise<CoverageResponse> {
  const response = await apiClient.get<CoverageResponse>(
    `/agents/${agentId}/coverage`
  )
  const validated = CoverageResponseSchema.parse(response.data)
  return validated
}

// Re-export types for convenience
export type { CoverageResponse }
