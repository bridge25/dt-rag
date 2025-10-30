// @CODE:AGENT-CARD-001-HOOK-001
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import type { AgentCardData } from '@/lib/api/types'

interface AgentsResponse {
  agents: AgentCardData[]
}

interface UseAgentsReturn {
  agents: AgentCardData[]
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<unknown>
}

async function fetchAgents(): Promise<AgentsResponse> {
  const { data } = await apiClient.get<AgentsResponse>('/agents')
  return data
}

export function useAgents(): UseAgentsReturn {
  const { data, isLoading, error, refetch } = useQuery<AgentsResponse, Error>({
    queryKey: ['agents'],
    queryFn: fetchAgents,
    retry: false,
    staleTime: 30000,
  })

  return {
    agents: data?.agents ?? [],
    isLoading,
    error: error ?? null,
    refetch,
  }
}
