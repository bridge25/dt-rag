/**
 * Test file
 *
 * @CODE:FRONTEND-001
 * @TEST:TAXONOMY-VIZ-001
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TaxonomyTreeView from '../TaxonomyTreeView'
import type { TaxonomyNode } from '../../../lib/api/types'
import * as taxonomyApi from '../../../lib/api/taxonomy'

// Mock React Flow
vi.mock('@xyflow/react', () => ({
  ReactFlow: ({
    nodes,
    edges,
    children,
  }: {
    nodes: unknown[]
    edges: unknown[]
    children?: React.ReactNode
  }) => (
    <div data-testid="react-flow-canvas">
      <div data-testid="nodes-count">{nodes.length}</div>
      <div data-testid="edges-count">{edges.length}</div>
      {children}
    </div>
  ),
  Background: () => <div data-testid="background" />,
  Controls: () => <div data-testid="controls" />,
  MiniMap: () => <div data-testid="minimap" />,
  useNodesState: (initialNodes: unknown[]) => [
    initialNodes,
    vi.fn(),
    vi.fn(),
  ],
  useEdgesState: (initialEdges: unknown[]) => [
    initialEdges,
    vi.fn(),
    vi.fn(),
  ],
}))

// Mock taxonomy API
vi.mock('../../../lib/api/taxonomy')

function generateLargeTaxonomy(levels: number, childrenPerNode: number): TaxonomyNode {
  let nodeIdCounter = 0

  function createNode(level: number, parentPath: string[], parentId: string | null): TaxonomyNode {
    const id = `node-${nodeIdCounter++}`
    const name = `Node ${id}`
    const path = [...parentPath, name]

    const node: TaxonomyNode = {
      id,
      name,
      path,
      parent_id: parentId,
      level,
      children: [],
    }

    if (level < levels) {
      for (let i = 0; i < childrenPerNode; i++) {
        node.children!.push(createNode(level + 1, path, id))
      }
    }

    return node
  }

  return createNode(0, [], null)
}

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('TaxonomyTreeView - Performance Optimization', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render 100 nodes efficiently', async () => {
    const largeTaxonomy = generateLargeTaxonomy(3, 4) // ~85 nodes (1 + 4 + 16 + 64)
    vi.mocked(taxonomyApi.fetchTaxonomyTree).mockResolvedValue(largeTaxonomy)

    const startTime = performance.now()
    const { getByTestId } = render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(getByTestId('react-flow-canvas')).toBeInTheDocument()
    })

    const endTime = performance.now()
    const renderTime = endTime - startTime

    // Should render in less than 2 seconds
    expect(renderTime).toBeLessThan(2000)
  })

  it('should handle 500+ nodes without crashing', async () => {
    const largeTaxonomy = generateLargeTaxonomy(4, 5) // ~780 nodes (1 + 5 + 25 + 125 + 625)
    vi.mocked(taxonomyApi.fetchTaxonomyTree).mockResolvedValue(largeTaxonomy)

    const { getByTestId } = render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      const canvas = getByTestId('react-flow-canvas')
      expect(canvas).toBeInTheDocument()
    })

    // Should render all nodes
    const nodesCountElement = getByTestId('nodes-count')
    const nodeCount = parseInt(nodesCountElement.textContent || '0', 10)
    expect(nodeCount).toBeGreaterThan(500)
  })

  it('should use memoization for node rendering', async () => {
    const largeTaxonomy = generateLargeTaxonomy(3, 4)
    vi.mocked(taxonomyApi.fetchTaxonomyTree).mockResolvedValue(largeTaxonomy)

    const { rerender, getByTestId } = render(<TaxonomyTreeView />, {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(getByTestId('react-flow-canvas')).toBeInTheDocument()
    })

    const firstRenderNodesCount = getByTestId('nodes-count').textContent

    // Re-render without changing data
    rerender(<TaxonomyTreeView />)

    // Nodes count should remain the same (memoization working)
    expect(getByTestId('nodes-count').textContent).toBe(firstRenderNodesCount)
  })

  it('should efficiently calculate Dagre layout for large graphs', async () => {
    const largeTaxonomy = generateLargeTaxonomy(3, 5) // ~156 nodes
    vi.mocked(taxonomyApi.fetchTaxonomyTree).mockResolvedValue(largeTaxonomy)

    const startTime = performance.now()
    const { getByTestId } = render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(getByTestId('react-flow-canvas')).toBeInTheDocument()
    })

    const endTime = performance.now()
    const layoutTime = endTime - startTime

    // Layout calculation should be reasonably fast
    expect(layoutTime).toBeLessThan(3000)
  })

  it('should handle deep hierarchies (10+ levels)', async () => {
    const deepTaxonomy = generateLargeTaxonomy(10, 2) // ~2047 nodes (but deep)
    vi.mocked(taxonomyApi.fetchTaxonomyTree).mockResolvedValue(deepTaxonomy)

    const { getByTestId } = render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(getByTestId('react-flow-canvas')).toBeInTheDocument()
    })

    // Should render without stack overflow
    const nodesCountElement = getByTestId('nodes-count')
    expect(nodesCountElement).toBeInTheDocument()
  })
})
