import {
  TaxonomyNode,
  TaxonomyTree,
  TaxonomyVersion,
  TaxonomyStatistics,
  TaxonomyVersionsResponse,
  VersionComparison,
  TaxonomyTreeSchema,
  TaxonomyVersionsResponseSchema,
  TaxonomyStatisticsSchema,
  TaxonomyNodeSchema,
  VersionComparisonSchema,
} from '@/types/schemas'
import { apiCache, CACHE_TTL } from '@/lib/cache'
import { handleApiResponse } from '@/lib/errorHandler'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1'
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || ''

if (!process.env.NEXT_PUBLIC_API_KEY) {
  console.warn(
    '[TaxonomyService] API key not configured. Please set NEXT_PUBLIC_API_KEY in .env.local'
  )
}

export type { TaxonomyNode, TaxonomyTree, TaxonomyVersion, TaxonomyStatistics, VersionComparison }

class TaxonomyService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
        ...options?.headers,
      },
    })

    return handleApiResponse<T>(response)
  }

  async getVersions(page: number = 1, limit: number = 20): Promise<TaxonomyVersionsResponse> {
    const cacheKey = `taxonomy:versions:${page}:${limit}`
    const cached = apiCache.get<TaxonomyVersionsResponse>(cacheKey)

    if (cached) {
      return cached
    }

    const data = await this.request<unknown>(
      `/taxonomy/versions?page=${page}&limit=${limit}`
    )
    const parsed = TaxonomyVersionsResponseSchema.parse(data)

    apiCache.set(cacheKey, parsed, CACHE_TTL.TAXONOMY_VERSIONS)
    return parsed
  }

  async getTree(version: string): Promise<TaxonomyTree> {
    const cacheKey = `taxonomy:tree:${version}`
    const cached = apiCache.get<TaxonomyTree>(cacheKey)

    if (cached) {
      return cached
    }

    const data = await this.request<unknown>(`/taxonomy/${version}/tree`)
    const parsed = TaxonomyTreeSchema.parse(data)

    apiCache.set(cacheKey, parsed, CACHE_TTL.TAXONOMY_TREE)
    return parsed
  }

  async getStatistics(version: string): Promise<TaxonomyStatistics> {
    const cacheKey = `taxonomy:statistics:${version}`
    const cached = apiCache.get<TaxonomyStatistics>(cacheKey)

    if (cached) {
      return cached
    }

    const data = await this.request<unknown>(`/taxonomy/${version}/statistics`)
    const parsed = TaxonomyStatisticsSchema.parse(data)

    apiCache.set(cacheKey, parsed, CACHE_TTL.TAXONOMY_STATISTICS)
    return parsed
  }

  async searchNodes(version: string, query: string, limit: number = 20): Promise<TaxonomyNode[]> {
    const cacheKey = `taxonomy:search:${version}:${query}:${limit}`
    const cached = apiCache.get<TaxonomyNode[]>(cacheKey)

    if (cached) {
      return cached
    }

    const data = await this.request<unknown>(
      `/taxonomy/${version}/search?q=${encodeURIComponent(query)}&limit=${limit}`
    )
    const parsed = TaxonomyNodeSchema.array().parse(data)

    apiCache.set(cacheKey, parsed, CACHE_TTL.TAXONOMY_SEARCH)
    return parsed
  }

  async compareVersions(baseVersion: string, targetVersion: string): Promise<VersionComparison> {
    const cacheKey = `taxonomy:compare:${baseVersion}:${targetVersion}`
    const cached = apiCache.get<VersionComparison>(cacheKey)

    if (cached) {
      return cached
    }

    const data = await this.request<unknown>(
      `/taxonomy/${baseVersion}/compare/${targetVersion}`
    )
    const parsed = VersionComparisonSchema.parse(data)

    apiCache.set(cacheKey, parsed, CACHE_TTL.TAXONOMY_COMPARISON)
    return parsed
  }
}

export const taxonomyService = new TaxonomyService()
