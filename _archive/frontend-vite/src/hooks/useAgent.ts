/**
 * Hook for fetching single agent data
 *
 * @CODE:FRONTEND-001
 */
import { useQuery } from '@tanstack/react-query'
import { fetchAgent } from '@/lib/api/agents'
import type { AgentCardData } from '@/lib/api/types'

interface UseAgentReturn {
  agent: AgentCardData | undefined
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<unknown>
}

export function useAgent(agentId: string): UseAgentReturn {
  const { data, isLoading, error, refetch } = useQuery<AgentCardData, Error>({
    queryKey: ['agent', agentId],
    queryFn: () => fetchAgent(agentId),
    staleTime: 30000,
  })

  return {
    agent: data,
    isLoading,
    error: error ?? null,
    refetch,
  }
}
