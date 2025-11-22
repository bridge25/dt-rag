/**
 * Hook for fetching list of agents
 *
 * @CODE:FRONTEND-001
 */
import { useQuery } from '@tanstack/react-query'
import { fetchAgents, type FetchAgentsParams } from '@/lib/api/agents'
import type { AgentCardData } from '@/lib/api/types'

interface UseAgentsReturn {
  agents: AgentCardData[]
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<unknown>
}

export function useAgents(params?: FetchAgentsParams): UseAgentsReturn {
  const { data, isLoading, error, refetch } = useQuery<AgentCardData[], Error>({
    queryKey: ['agents', params],
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
