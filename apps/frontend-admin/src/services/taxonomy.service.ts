import { apiClient } from './api-client'
import { API_ENDPOINTS } from '@/constants/api'
import type { TaxonomyTree } from '@/types/common'

class TaxonomyService {
  async getVersions(): Promise<string[]> {
    try {
      const response = await apiClient.get<string[]>(API_ENDPOINTS.TAXONOMY.VERSIONS)
      return response.data
    } catch (error) {
      console.error('Failed to fetch taxonomy versions:', error)
      throw error
    }
  }

  async getTree(version: string): Promise<TaxonomyTree> {
    try {
      const response = await apiClient.get<TaxonomyTree>(
        `${API_ENDPOINTS.TAXONOMY.TREE}/${version}`
      )
      return response.data
    } catch (error) {
      console.error(`Failed to fetch taxonomy tree for version ${version}:`, error)
      throw error
    }
  }

  async searchNodes(query: string, version?: string): Promise<TaxonomyTree> {
    try {
      const params = version ? { version } : {}
      const response = await apiClient.get<TaxonomyTree>(
        API_ENDPOINTS.TAXONOMY.SEARCH,
        { ...params, q: query }
      )
      return response.data
    } catch (error) {
      console.error(`Failed to search taxonomy nodes for query "${query}":`, error)
      throw error
    }
  }
}

export const taxonomyService = new TaxonomyService()