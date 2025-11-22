/**
 * Test file to verify all imports are resolvable
 *
 * @CODE:FRONTEND-001
 */

import type { SearchRequest, TaxonomyNode } from '@/lib/api/types'
import { apiClient } from '@/lib/api/client'
import { env } from '@/lib/env'
import { cn } from '@/lib/utils'

// Test that all imports resolve
console.log('All imports successful')

// Verify types are available
const testRequest: SearchRequest = {
  q: 'test',
  max_results: 10,
  include_highlights: true,
  search_mode: 'hybrid',
}

const testNode: TaxonomyNode = {
  id: '1',
  name: 'test',
  path: ['test'],
  parent_id: null,
  level: 0,
}

// Verify functions work
const testClassName = cn('test-class')

console.log({ testRequest, testNode, testClassName, apiClient, env })
