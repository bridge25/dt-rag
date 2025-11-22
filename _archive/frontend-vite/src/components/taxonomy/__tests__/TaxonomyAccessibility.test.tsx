/**
 * Accessibility test for WCAG 2.1 AA compliant focus indicators
 * Tests: axe-core audit, focus indicator visibility, color contrast
 *
 * @CODE:FRONTEND-001
 * @TEST:TAXONOMY-VIZ-001
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TaxonomyTreeView from '../TaxonomyTreeView'
import TaxonomySearchFilter from '../TaxonomySearchFilter'
import TaxonomyLayoutToggle from '../TaxonomyLayoutToggle'
import TaxonomyNode from '../TaxonomyNode'
import TaxonomyDetailPanel from '../TaxonomyDetailPanel'
import type { TaxonomyNode as TaxonomyNodeType } from '../../../lib/api/types'
import * as taxonomyApi from '../../../lib/api/taxonomy'

// Extend Jest matchers
expect.extend(toHaveNoViolations)

// Mock React Flow
vi.mock('@xyflow/react', () => ({
  ReactFlow: ({ children }: { nodes?: unknown[]; edges?: unknown[]; children?: React.ReactNode }) => (
    <div data-testid="react-flow-canvas">
      {children}
    </div>
  ),
  Background: () => <div data-testid="background" />,
  Controls: () => (
    <div data-testid="controls">
      <button aria-label="zoom in">+</button>
      <button aria-label="fit view">fit</button>
      <button aria-label="zoom out">-</button>
    </div>
  ),
  MiniMap: () => <div data-testid="minimap" />,
  useNodesState: (initialNodes: unknown[]) => [initialNodes, vi.fn(), vi.fn()],
  useEdgesState: (initialEdges: unknown[]) => [initialEdges, vi.fn(), vi.fn()],
  Handle: () => null,
  Position: {
    Top: 'top',
    Bottom: 'bottom',
    Left: 'left',
    Right: 'right',
  },
}))

const mockTaxonomyData: TaxonomyNodeType = {
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

describe('Taxonomy Components - Accessibility (WCAG 2.1 AA)', () => {
  beforeEach(() => {
    vi.mocked(taxonomyApi.fetchTaxonomyTree).mockResolvedValue(mockTaxonomyData)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('should have no axe violations in TaxonomyTreeView', async () => {
    const { container } = render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search taxonomy nodes...')).toBeInTheDocument()
    })

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('should have no axe violations in TaxonomySearchFilter', async () => {
    const onSearch = vi.fn()
    const { container } = render(
      <TaxonomySearchFilter onSearch={onSearch} matchCount={0} />
    )

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('should have no axe violations in TaxonomyLayoutToggle', async () => {
    const onLayoutChange = vi.fn()
    const { container } = render(
      <TaxonomyLayoutToggle currentLayout="tree" onLayoutChange={onLayoutChange} />
    )

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('should have no axe violations in TaxonomyNode', async () => {
    const mockNodeData = {
      taxonomyNode: mockTaxonomyData,
      isExpanded: true,
    }

    const { container } = render(
      <TaxonomyNode
        id="test-node"
        data={mockNodeData}
        type="taxonomyNode"
        selected={false}
        isConnectable={true}
        zIndex={1}
        xPos={0}
        yPos={0}
        dragging={false}
      />
    )

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('should have no axe violations in TaxonomyDetailPanel', async () => {
    const onClose = vi.fn()
    const { container } = render(
      <TaxonomyDetailPanel node={mockTaxonomyData} onClose={onClose} />
    )

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('should have focus-visible styles on search input', () => {
    const onSearch = vi.fn()
    render(<TaxonomySearchFilter onSearch={onSearch} matchCount={0} />)

    const searchInput = screen.getByPlaceholderText('Search taxonomy nodes...')
    expect(searchInput.className).toContain('focus:')
  })

  it('should have focus-visible styles on layout toggle button', () => {
    const onLayoutChange = vi.fn()
    render(
      <TaxonomyLayoutToggle currentLayout="tree" onLayoutChange={onLayoutChange} />
    )

    const button = screen.getByRole('button', { name: /Switch to Radial layout/i })
    expect(button.className).toContain('focus:')
  })

  it('should have focus-visible styles on taxonomy nodes', () => {
    const mockNodeData = {
      taxonomyNode: mockTaxonomyData,
      isExpanded: true,
    }

    render(
      <TaxonomyNode
        id="test-node"
        data={mockNodeData}
        type="taxonomyNode"
        selected={false}
        isConnectable={true}
        zIndex={1}
        xPos={0}
        yPos={0}
        dragging={false}
      />
    )

    const nodeElement = screen.getByRole('button', { name: /Taxonomy node: Root Category/i })
    expect(nodeElement.className).toContain('focus-visible:')
  })

  it('should have focus styles on detail panel close button', () => {
    const onClose = vi.fn()
    render(<TaxonomyDetailPanel node={mockTaxonomyData} onClose={onClose} />)

    const closeButton = screen.getByRole('button', { name: 'Close detail panel' })
    expect(closeButton.className).toContain('focus:')
  })

  it('should not have outline: none without replacement', () => {
    const onSearch = vi.fn()
    render(<TaxonomySearchFilter onSearch={onSearch} matchCount={0} />)

    const searchInput = screen.getByPlaceholderText('Search taxonomy nodes...')
    const styles = window.getComputedStyle(searchInput)

    // If outline is none, there should be alternative focus styles (ring, border, etc.)
    if (styles.outline === 'none' || styles.outlineWidth === '0px') {
      // Check for Tailwind ring or border classes in className
      expect(searchInput.className).toMatch(/focus:(ring|border)/)
    }
  })

  it('should have consistent focus styles across all interactive elements', async () => {
    const { container } = render(<TaxonomyTreeView />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search taxonomy nodes...')).toBeInTheDocument()
    })

    const interactiveElements = container.querySelectorAll('button, input, [role="button"]')
    expect(interactiveElements.length).toBeGreaterThan(0)

    // All interactive elements should have focus styles
    interactiveElements.forEach((element) => {
      const className = element.getAttribute('class') || ''
      expect(className).toMatch(/focus(-visible)?:/)
    })
  })

  it('should have focus indicator with minimum 2px width', () => {
    const mockNodeData = {
      taxonomyNode: mockTaxonomyData,
      isExpanded: true,
    }

    render(
      <TaxonomyNode
        id="test-node"
        data={mockNodeData}
        type="taxonomyNode"
        selected={false}
        isConnectable={true}
        zIndex={1}
        xPos={0}
        yPos={0}
        dragging={false}
      />
    )

    const nodeElement = screen.getByRole('button', { name: /Taxonomy node: Root Category/i })

    // Check for Tailwind outline-2 class (2px outline)
    expect(nodeElement.className).toContain('outline-2')
  })

  it('should have visible focus indicators when elements are focused', async () => {
    const onSearch = vi.fn()
    render(<TaxonomySearchFilter onSearch={onSearch} matchCount={0} />)

    const searchInput = screen.getByPlaceholderText('Search taxonomy nodes...')
    searchInput.focus()

    expect(searchInput).toHaveFocus()

    // In a real browser, focus styles would be visible
    // In JSDOM, we verify the classes are present
    expect(searchInput.className).toContain('focus:')
  })
})
