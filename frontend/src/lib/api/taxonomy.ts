// @CODE:TAXONOMY-VIZ-001-002
// Taxonomy API client for fetching taxonomy tree structure

import { apiClient } from './client'
import type { TaxonomyNode } from './types'
import { TaxonomyNodeSchema } from './types'

export interface FetchTaxonomyTreeParams {
  include_metadata?: boolean
  max_depth?: number
}

export async function fetchTaxonomyTree(
  params?: FetchTaxonomyTreeParams
): Promise<TaxonomyNode> {
  const response = await apiClient.get<TaxonomyNode>(
    '/api/taxonomy/tree',
    params as Record<string, unknown>
  )
  const validated = TaxonomyNodeSchema.parse(response)
  return validated
}
