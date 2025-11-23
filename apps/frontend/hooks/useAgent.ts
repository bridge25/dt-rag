/**
 * Hook for fetching single agent data
 *
 * @CODE:FRONTEND-MIGRATION-002
 */
"use client"

import { useQuery } from "@tanstack/react-query"
import { fetchAgent } from "@/lib/api/agents"
import type { AgentCardData } from "@/lib/api/types"

interface UseAgentReturn {
  agent: AgentCardData | undefined
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<unknown>
}

export function useAgent(agentId: string): UseAgentReturn {
  const { data, isLoading, error, refetch } = useQuery<AgentCardData, Error>({
    queryKey: ["agent", agentId],
    queryFn: () => fetchAgent(agentId),
    staleTime: 30000,
    enabled: !!agentId,
  })

  // Guard refetch to prevent calling with falsy agentId
  const safeRefetch = async () => {
    if (!agentId) {
      return Promise.resolve(undefined)
    }
    return refetch()
  }

  return {
    agent: data,
    isLoading,
    error: error ?? null,
    refetch: safeRefetch,
  }
}
