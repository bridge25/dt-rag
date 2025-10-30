// @CODE:AGENT-CARD-001-HOOK-001
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import { AgentCardDataSchema, type AgentCardData } from '@/lib/api/types'
import { z } from 'zod'

const AgentsResponseSchema = z.object({
  agents: z.array(AgentCardDataSchema),
})

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

  // Validate response data with Zod
  try {
    const validated = AgentsResponseSchema.parse(data)
    return validated
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error('Agent data validation failed:', error.errors)
      throw new Error(`Invalid agent data: ${error.errors.map(e => e.message).join(', ')}`)
    }
    throw error
  }
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
