/**
 * Hook for fetching list of agents with Pokemon-style card data
 *
 * @CODE:FRONTEND-MIGRATION-001
 */
"use client"

import { useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/api/client"
import { AgentCardDataSchema, AgentCardListResponseSchema } from "@/lib/api/types"
import type { AgentCardData, AgentCardListResponse } from "@/lib/api/types"

interface FetchAgentsParams {
  level?: number
  min_coverage?: number
  max_results?: number
}

interface UseAgentsReturn {
  agents: AgentCardData[]
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<unknown>
}

async function fetchAgents(params?: FetchAgentsParams): Promise<AgentCardData[]> {
  const response = await apiClient.get<AgentCardListResponse>("/agents/", { params })
  const validated = AgentCardListResponseSchema.parse(response.data)
  return validated.agents
}

export function useAgents(params?: FetchAgentsParams): UseAgentsReturn {
  const { data, isLoading, error, refetch } = useQuery<AgentCardData[], Error>({
    queryKey: ["agents", params],
    queryFn: () => fetchAgents(params),
    retry: false,
    staleTime: 30000,
  })

  return {
    agents: data ?? [],
    isLoading,
    error: error ?? null,
    refetch,
  }
}
