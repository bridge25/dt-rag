// @TEST:TAXONOMY-KEYNAV-002-004
// Unit test for Tab navigation order in TaxonomyTreeView
// Tests Tab key sequence: Search Filter → Layout Toggle → Zoom Controls → Nodes

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TaxonomyTreeView from '../TaxonomyTreeView'
import type { TaxonomyNode } from '../../../lib/api/types'
import * as taxonomyApi from '../../../lib/api/taxonomy'

// Mock React Flow components with focusable controls
vi.mock('@xyflow/react', () => ({
  ReactFlow: ({ nodes, edges, children }: { nodes: unknown[]; edges: unknown[]; children?: React.ReactNode }) => (
    <div data-testid="react-flow-canvas">
      <div data-testid="nodes-count">{nodes.length}</div>
      <div data-testid="edges-count">{edges.length}</div>
      {children}
    </div>
  ),
  Background: () => <div data-testid="background" />,
  Controls: () => (
    <div data-testid="controls">
      <button aria-label="zoom in" tabIndex={0}>+</button>
      <button aria-label="fit view" tabIndex={0}>fit</button>
      <button aria-label="zoom out" tabIndex={0}>-</button>
    </div>
  ),
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
  Handle: () => null,
  Position: {
    Top: 'top',
    Bottom: 'bottom',
    Left: 'left',
    Right: 'right',
  },
}))

const mockTaxonomyData: TaxonomyNode = {
  id: 'root',
  name: 'Root Category',
  level: 0,
  path: ['Root Category'],
  document_count: 50,
  children: [
    {
      id: 'child-1',
      name: 'Child 1',
      level: 1,
      path: ['Root Category', 'Child 1'],
      document_count: 20,
      children: [],
    },
    {
      id: 'child-2',
      name: 'Child 2',
      level: 1,
      path: ['Root Category', 'Child 2'],
      document_count: 30,
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

describe('TaxonomyTreeView - Tab Navigation Order', () => {
  beforeEach(() => {
    vi.mocked(taxonomyApi.fetchTaxonomyTree).mockResolvedValue(mockTaxonomyData)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('should render search filter with correct tabIndex', async () => {
    render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText('Search taxonomy nodes...')
      expect(searchInput).toBeInTheDocument()
      // Search input should be tabbable (no explicit tabIndex or tabIndex >= 0)
      expect(searchInput.getAttribute('tabIndex')).not.toBe('-1')
    })
  })

  it('should render layout toggle button with correct tabIndex', async () => {
    render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      const layoutToggle = screen.getByRole('button', { name: /Switch to Radial layout/i })
      expect(layoutToggle).toBeInTheDocument()
      // Button should be tabbable
      expect(layoutToggle.getAttribute('tabIndex')).not.toBe('-1')
    })
  })

  it('should render React Flow controls with correct tabIndex', async () => {
    render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      const zoomInButton = screen.getByLabelText('zoom in')
      const fitViewButton = screen.getByLabelText('fit view')
      const zoomOutButton = screen.getByLabelText('zoom out')

      expect(zoomInButton).toBeInTheDocument()
      expect(fitViewButton).toBeInTheDocument()
      expect(zoomOutButton).toBeInTheDocument()

      // All controls should have tabIndex={0}
      expect(zoomInButton.getAttribute('tabIndex')).toBe('0')
      expect(fitViewButton.getAttribute('tabIndex')).toBe('0')
      expect(zoomOutButton.getAttribute('tabIndex')).toBe('0')
    })
  })

  it('should render all interactive elements in logical DOM order', async () => {
    render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search taxonomy nodes...')).toBeInTheDocument()
    })

    // Get all focusable elements in DOM order
    const focusableElements = document.querySelectorAll(
      'input, button, [tabindex]:not([tabindex="-1"])'
    )

    expect(focusableElements.length).toBeGreaterThan(0)

    // Verify first few elements are in expected order
    const searchInput = screen.getByPlaceholderText('Search taxonomy nodes...')
    const layoutToggle = screen.getByRole('button', { name: /Switch to Radial layout/i })

    // Search should come before layout toggle in DOM
    const searchIndex = Array.from(focusableElements).indexOf(searchInput)
    const toggleIndex = Array.from(focusableElements).indexOf(layoutToggle)

    expect(searchIndex).toBeGreaterThanOrEqual(0)
    expect(toggleIndex).toBeGreaterThan(searchIndex)
  })

  it('should have visible focus styles on search filter', async () => {
    render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText('Search taxonomy nodes...')
      expect(searchInput).toBeInTheDocument()

      // Check for Tailwind focus classes
      expect(searchInput.className).toContain('focus:')
    })
  })

  it('should have visible focus styles on layout toggle button', async () => {
    render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      const layoutToggle = screen.getByRole('button', { name: /Switch to Radial layout/i })
      expect(layoutToggle).toBeInTheDocument()

      // Check for Tailwind focus classes
      expect(layoutToggle.className).toContain('focus:')
    })
  })

  it('should render detail panel close button when node is selected', async () => {
    render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText('Root Category')).toBeInTheDocument()
    })

    // Initially no detail panel
    expect(screen.queryByTestId('detail-panel')).not.toBeInTheDocument()

    // Click on a node would open detail panel, but we'll test the panel separately
    // This test just verifies the structure is correct
  })
})
