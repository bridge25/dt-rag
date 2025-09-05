import useSWR from 'swr'
import { apiClient } from '@/services/api-client'
import type { TaxonomyTree, ApiResponse } from '@/types/common'

const fetcher = async (url: string) => {
  const response = await apiClient.get<any>(url)
  return response.data
}

export function useTaxonomyTree(version: string) {
  return useSWR(
    version ? `/api/taxonomy/${version}/tree` : null,
    fetcher,
    {
      dedupingInterval: 600_000,    // 10 minutes cache
      revalidateOnFocus: false,     // Don't refetch on window focus
      revalidateOnReconnect: true,  // Refetch when reconnected
      errorRetryCount: 3,           // Retry failed requests 3 times
      errorRetryInterval: 5000,     // Wait 5s between retries
    }
  )
}

export function useTaxonomyVersions() {
  return useSWR(
    '/api/taxonomy/versions',
    fetcher,
    {
      dedupingInterval: 300_000,    // 5 minutes cache
      revalidateOnFocus: false,
    }
  )
}

export function useTaxonomySearch(query: string, filters?: Record<string, any>) {
  const searchKey = query ? `/api/taxonomy/search?q=${encodeURIComponent(query)}${filters ? '&' + new URLSearchParams(filters).toString() : ''}` : null
  
  return useSWR(
    searchKey,
    fetcher,
    {
      dedupingInterval: 60_000,     // 1 minute cache for searches
      revalidateOnFocus: false,
    }
  )
}