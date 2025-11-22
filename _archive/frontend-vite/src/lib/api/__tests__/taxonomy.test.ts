/**
 * Test file
 *
 * @CODE:FRONTEND-001
 * @TEST:FRONTEND-001
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fetchTaxonomyTree } from '../taxonomy'
import { apiClient } from '../client'
import type { TaxonomyNode } from '../types'

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}))

describe('Taxonomy API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchTaxonomyTree', () => {
    it('should fetch taxonomy tree from correct endpoint', async () => {
      const mockTree: TaxonomyNode = {
        id: 'root',
        name: 'Root',
        path: ['Root'],
        parent_id: null,
        level: 0,
        children: [],
      }

      vi.mocked(apiClient.get).mockResolvedValue(mockTree)

      const result = await fetchTaxonomyTree()

      expect(apiClient.get).toHaveBeenCalledWith('/api/taxonomy/tree', undefined)
      expect(result).toEqual(mockTree)
    })

    it('should return nested taxonomy structure with children', async () => {
      const mockTree: TaxonomyNode = {
        id: 'root',
        name: 'Root',
        path: ['Root'],
        parent_id: null,
        level: 0,
        children: [
          {
            id: 'child1',
            name: 'Child 1',
            path: ['Root', 'Child 1'],
            parent_id: 'root',
            level: 1,
            children: [],
          },
        ],
      }

      vi.mocked(apiClient.get).mockResolvedValue(mockTree)

      const result = await fetchTaxonomyTree()

      expect(result.children).toBeDefined()
      expect(result.children?.length).toBe(1)
      expect(result.children?.[0].name).toBe('Child 1')
    })

    it('should handle taxonomy tree with metadata', async () => {
      const mockTree: TaxonomyNode = {
        id: 'root',
        name: 'Root',
        path: ['Root'],
        parent_id: null,
        level: 0,
        metadata: {
          documentCount: 150,
          color: '#3498db',
        },
        children: [],
      }

      vi.mocked(apiClient.get).mockResolvedValue(mockTree)

      const result = await fetchTaxonomyTree()

      expect(result.metadata).toBeDefined()
      expect(result.metadata?.documentCount).toBe(150)
    })

    it('should handle API errors gracefully', async () => {
      const mockError = new Error('Network Error')
      vi.mocked(apiClient.get).mockRejectedValue(mockError)

      await expect(fetchTaxonomyTree()).rejects.toThrow('Network Error')
    })

    it('should validate response structure with TaxonomyNodeSchema', async () => {
      const mockTree: TaxonomyNode = {
        id: 'root',
        name: 'Root',
        path: ['Root'],
        parent_id: null,
        level: 0,
        children: [],
      }

      vi.mocked(apiClient.get).mockResolvedValue(mockTree)

      const result = await fetchTaxonomyTree()

      expect(result).toHaveProperty('id')
      expect(result).toHaveProperty('name')
      expect(result).toHaveProperty('path')
      expect(result).toHaveProperty('parent_id')
      expect(result).toHaveProperty('level')
    })
  })
})
