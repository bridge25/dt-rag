// @CODE:FRONTEND-INTEGRATION-001:HISTORY-HOOK
import { useQuery } from '@tanstack/react-query'
import { fetchCoverageHistory, type CoverageHistoryResponse } from '@/lib/api/history'

interface UseCoverageHistoryParams {
  start_date?: string
  end_date?: string
  interval?: 'daily' | 'weekly' | 'monthly'
}

interface UseCoverageHistoryReturn {
  data: CoverageHistoryResponse | undefined
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<unknown>
}

export function useCoverageHistory(
  agentId: string,
  params?: UseCoverageHistoryParams
): UseCoverageHistoryReturn {
  const { data, isLoading, error, refetch } = useQuery<CoverageHistoryResponse, Error>({
    queryKey: ['coverageHistory', agentId, params],
    queryFn: () => fetchCoverageHistory(agentId, params),
    retry: 1,
    staleTime: 60000,
  })

  return {
    data,
    isLoading,
    error: error ?? null,
    refetch,
  }
}
