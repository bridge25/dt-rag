// @CODE:FRONTEND-INTEGRATION-001:AGENTS-API
import { apiClient } from './client'
import type { AgentCardData } from './types'
import { AgentCardDataSchema } from './types'
import { z } from 'zod'

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

export interface CoverageResponse {
  agent_id: string
  coverage_percentage: number
  total_documents: number
  covered_documents: number
  taxonomy_depth: number
}

export async function fetchAgents(params?: FetchAgentsParams): Promise<AgentCardData[]> {
  const response = await apiClient.get<AgentsListResponse>('/api/v1/agents', params)
  const validated = AgentsListResponseSchema.parse(response)
  return validated.agents
}

export async function fetchAgent(agentId: string): Promise<AgentCardData> {
  return apiClient.get<AgentCardData>(`/api/v1/agents/${agentId}`)
}

export async function calculateCoverage(agentId: string): Promise<CoverageResponse> {
  return apiClient.get<CoverageResponse>(`/api/v1/agents/${agentId}/coverage`)
}
