// @TEST:TAXONOMY-VIZ-001-007
// TaxonomyTreeView interaction tests - node selection and highlighting

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TaxonomyTreeView from '../TaxonomyTreeView'
import type { TaxonomyNode } from '../../../lib/api/types'
import * as taxonomyApi from '../../../lib/api/taxonomy'

// Mock React Flow
vi.mock('@xyflow/react', () => ({
  ReactFlow: ({
    nodes,
    onNodeClick,
    children,
  }: {
    nodes: Array<{ id: string; selected?: boolean; data: { taxonomyNode: TaxonomyNode } }>
    edges?: unknown[]
    onNodeClick?: (event: unknown, node: { id: string; data: { taxonomyNode: TaxonomyNode } }) => void
    children?: React.ReactNode
  }) => (
    <div data-testid="react-flow-canvas">
      <div data-testid="nodes-container">
        {nodes.map((node) => (
          <div
            key={node.id}
            data-testid={`node-${node.id}`}
            data-selected={node.selected}
            onClick={() => onNodeClick?.(null, node)}
          >
            {node.data.taxonomyNode.name}
          </div>
        ))}
      </div>
      {children}
    </div>
  ),
  Background: () => <div data-testid="background" />,
  Controls: () => <div data-testid="controls" />,
  MiniMap: () => <div data-testid="minimap" />,
  useNodesState: (initialNodes: unknown[]) => {
    const [nodes, setNodes] = vi.fn(() => [initialNodes, vi.fn()])() as [unknown[], (nodes: unknown[]) => void]
    return [nodes, setNodes, vi.fn()]
  },
  useEdgesState: (initialEdges: unknown[]) => [
    initialEdges,
    vi.fn(),
    vi.fn(),
  ],
}))

// Mock taxonomy API
vi.mock('../../../lib/api/taxonomy')

const mockTaxonomyData: TaxonomyNode = {
  id: 'root',
  name: 'Root',
  path: ['Root'],
  parent_id: null,
  level: 0,
  children: [
    {
      id: 'child1',
      name: 'Technology',
      path: ['Root', 'Technology'],
      parent_id: 'root',
      level: 1,
      children: [],
    },
    {
      id: 'child2',
      name: 'Science',
      path: ['Root', 'Science'],
      parent_id: 'root',
      level: 1,
      children: [],
    },
  ],
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

describe('TaxonomyTreeView - Node Selection & Highlighting', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should handle node click events', async () => {
    vi.mocked(taxonomyApi.fetchTaxonomyTree).mockResolvedValue(mockTaxonomyData)

    render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByTestId('node-child1')).toBeInTheDocument()
    })

    const node = screen.getByTestId('node-child1')
    await userEvent.click(node)

    // Node should be clickable
    expect(node).toBeInTheDocument()
  })

  it('should display detail panel when node is selected', async () => {
    vi.mocked(taxonomyApi.fetchTaxonomyTree).mockResolvedValue(mockTaxonomyData)

    render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByTestId('node-child1')).toBeInTheDocument()
    })

    const node = screen.getByTestId('node-child1')
    await userEvent.click(node)

    await waitFor(() => {
      expect(screen.getByTestId('detail-panel')).toBeInTheDocument()
    })
  })

  it('should show node details in detail panel', async () => {
    vi.mocked(taxonomyApi.fetchTaxonomyTree).mockResolvedValue(mockTaxonomyData)

    render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByTestId('node-child1')).toBeInTheDocument()
    })

    const node = screen.getByTestId('node-child1')
    await userEvent.click(node)

    await waitFor(() => {
      expect(screen.getByText('Technology')).toBeInTheDocument()
      expect(screen.getByText(/level 1/i)).toBeInTheDocument()
    })
  })

  it('should allow deselecting node by clicking elsewhere', async () => {
    vi.mocked(taxonomyApi.fetchTaxonomyTree).mockResolvedValue(mockTaxonomyData)

    render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByTestId('node-child1')).toBeInTheDocument()
    })

    // Select node
    const node = screen.getByTestId('node-child1')
    await userEvent.click(node)

    await waitFor(() => {
      expect(screen.getByTestId('detail-panel')).toBeInTheDocument()
    })

    // Click close button
    const closeButton = screen.getByLabelText(/close detail panel/i)
    await userEvent.click(closeButton)

    await waitFor(() => {
      expect(screen.queryByTestId('detail-panel')).not.toBeInTheDocument()
    })
  })

  it('should switch selection when clicking different nodes', async () => {
    vi.mocked(taxonomyApi.fetchTaxonomyTree).mockResolvedValue(mockTaxonomyData)

    render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByTestId('node-child1')).toBeInTheDocument()
    })

    // Select first node
    const node1 = screen.getByTestId('node-child1')
    await userEvent.click(node1)

    await waitFor(() => {
      const detailPanel = screen.getByTestId('detail-panel')
      expect(detailPanel).toHaveTextContent('Technology')
    })

    // Select second node
    const node2 = screen.getByTestId('node-child2')
    await userEvent.click(node2)

    await waitFor(() => {
      const detailPanel = screen.getByTestId('detail-panel')
      expect(detailPanel).toHaveTextContent('Science')
    })
  })
})
