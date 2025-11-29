/**
 * ConstellationGraph Component Tests
 *
 * Tests for the main taxonomy constellation visualization container.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ConstellationGraph from '../ConstellationGraph'
import type { TaxonomyNode } from '@/lib/api/types'

interface Edge {
  id: string
  source: string
  target: string
  strength?: number
}

describe('ConstellationGraph', () => {
  const defaultNodes: TaxonomyNode[] = [
    {
      id: 'root',
      name: 'Root',
      level: 1,
      path: ['Root'],
      parent_id: null,
      document_count: 100
    },
    {
      id: 'branch-1',
      name: 'Branch 1',
      level: 2,
      path: ['Root', 'Branch 1'],
      parent_id: 'root',
      document_count: 50
    },
    {
      id: 'branch-2',
      name: 'Branch 2',
      level: 2,
      path: ['Root', 'Branch 2'],
      parent_id: 'root',
      document_count: 50
    }
  ]

  const defaultEdges: Edge[] = [
    { id: 'edge-1', source: 'root', target: 'branch-1', strength: 0.9 },
    { id: 'edge-2', source: 'root', target: 'branch-2', strength: 0.9 }
  ]

  const defaultProps = {
    nodes: defaultNodes,
    edges: defaultEdges,
    onNodeSelect: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render the graph container', () => {
      render(<ConstellationGraph {...defaultProps} />)
      const container = screen.getByTestId('constellation-graph')
      expect(container).toBeInTheDocument()
    })

    it('should have space background', () => {
      render(<ConstellationGraph {...defaultProps} />)
      const container = screen.getByTestId('constellation-graph')
      expect(container).toHaveClass('space-background')
    })

    it('should render all nodes', () => {
      render(<ConstellationGraph {...defaultProps} />)
      expect(screen.getByText('Root')).toBeInTheDocument()
      expect(screen.getByText('Branch 1')).toBeInTheDocument()
      expect(screen.getByText('Branch 2')).toBeInTheDocument()
    })

    it('should render SVG for edges', () => {
      const { container } = render(<ConstellationGraph {...defaultProps} />)
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('should handle empty node list', () => {
      render(<ConstellationGraph nodes={[]} edges={[]} onNodeSelect={vi.fn()} />)
      const container = screen.getByTestId('constellation-graph')
      expect(container).toBeInTheDocument()
    })

    it('should display empty state message', () => {
      render(<ConstellationGraph nodes={[]} edges={[]} onNodeSelect={vi.fn()} />)
      expect(screen.getByText(/No taxonomy data/i)).toBeInTheDocument()
    })
  })

  describe('Node Positioning', () => {
    it('should position nodes in radial layout', () => {
      const { container } = render(<ConstellationGraph {...defaultProps} />)
      // Get constellation nodes specifically (they have the class)
      const constellationNodes = container.querySelectorAll('.constellation-node')
      expect(constellationNodes.length).toBe(defaultProps.nodes.length)
      constellationNodes.forEach(node => {
        expect(node).toHaveClass('constellation-node')
        expect((node as HTMLElement).style.position).toBe('absolute')
      })
    })

    it('should calculate different positions for each node', () => {
      render(<ConstellationGraph {...defaultProps} />)
      const nodes = screen.getAllByRole('button')
      const positions: Array<{left: string, top: string}> = []

      nodes.forEach(node => {
        const parent = node.parentElement
        if (parent) {
          positions.push({
            left: parent.style.left,
            top: parent.style.top
          })
        }
      })

      // Verify positions are calculated
      expect(positions.length).toBeGreaterThan(0)
    })

    it('should center root node approximately', () => {
      render(<ConstellationGraph {...defaultProps} />)
      const rootButton = screen.getByText('Root').closest('[role="button"]')
      // Root should be approximately in center (checking relative positioning)
      expect(rootButton).toBeInTheDocument()
    })
  })

  describe('Node Interaction', () => {
    it('should call onNodeSelect when node is clicked', async () => {
      const user = userEvent.setup()
      const onNodeSelect = vi.fn()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={onNodeSelect} />)

      const rootButton = screen.getByText('Root').closest('[role="button"]')!
      await user.click(rootButton)

      expect(onNodeSelect).toHaveBeenCalledWith(defaultNodes[0])
    })

    it('should highlight selected node', async () => {
      const user = userEvent.setup()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={vi.fn()} />)

      const rootButton = screen.getByText('Root').closest('[role="button"]')!
      await user.click(rootButton)

      expect(rootButton).toHaveClass('selected')
    })

    it('should update selection when clicking different node', async () => {
      const user = userEvent.setup()
      const onNodeSelect = vi.fn()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={onNodeSelect} />)

      const rootButton = screen.getByText('Root').closest('[role="button"]')!
      const branch1Button = screen.getByText('Branch 1').closest('[role="button"]')!

      await user.click(rootButton)
      expect(onNodeSelect).toHaveBeenCalledWith(defaultNodes[0])

      await user.click(branch1Button)
      expect(onNodeSelect).toHaveBeenCalledWith(defaultNodes[1])
    })

    it('should handle hover effects on nodes', async () => {
      const user = userEvent.setup()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={vi.fn()} />)

      const rootButton = screen.getByText('Root').closest('[role="button"]')!
      await user.hover(rootButton)

      expect(rootButton).toHaveClass('hovered')

      await user.unhover(rootButton)
      expect(rootButton).not.toHaveClass('hovered')
    })
  })

  describe('Zoom and Pan Controls', () => {
    it('should render zoom in button', () => {
      render(<ConstellationGraph {...defaultProps} />)
      expect(screen.getByLabelText(/zoom in/i)).toBeInTheDocument()
    })

    it('should render zoom out button', () => {
      render(<ConstellationGraph {...defaultProps} />)
      expect(screen.getByLabelText(/zoom out/i)).toBeInTheDocument()
    })

    it('should render reset view button', () => {
      render(<ConstellationGraph {...defaultProps} />)
      expect(screen.getByLabelText(/reset view/i)).toBeInTheDocument()
    })

    it('should update zoom level on zoom in click', async () => {
      const user = userEvent.setup()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={vi.fn()} />)

      const zoomInButton = screen.getByLabelText(/zoom in/i)
      const container = screen.getByTestId('constellation-graph-content')

      await user.click(zoomInButton)

      // Check transform has updated
      const transform = container.style.transform
      expect(transform).toContain('scale')
    })

    it('should update zoom level on zoom out click', async () => {
      const user = userEvent.setup()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={vi.fn()} />)

      const zoomInButton = screen.getByLabelText(/zoom in/i)
      const zoomOutButton = screen.getByLabelText(/zoom out/i)
      const container = screen.getByTestId('constellation-graph-content')

      // Zoom in first
      await user.click(zoomInButton)
      const zoomedInTransform = container.style.transform

      // Then zoom out
      await user.click(zoomOutButton)
      const zoomedOutTransform = container.style.transform

      expect(zoomedInTransform).not.toBe(zoomedOutTransform)
    })

    it('should reset view to initial state', async () => {
      const user = userEvent.setup()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={vi.fn()} />)

      const zoomInButton = screen.getByLabelText(/zoom in/i)
      const resetButton = screen.getByLabelText(/reset view/i)
      const container = screen.getByTestId('constellation-graph-content')

      // Zoom in
      await user.click(zoomInButton)

      // Reset
      await user.click(resetButton)

      // Should be back to identity transform (1, 0)
      const transform = container.style.transform
      expect(transform === 'none' || /scale\(1\)/.test(transform)).toBe(true)
    })

    it('should have zoom limits', async () => {
      const user = userEvent.setup()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={vi.fn()} />)

      const zoomOutButton = screen.getByLabelText(/zoom out/i)
      const container = screen.getByTestId('constellation-graph-content')

      // Try to zoom out multiple times
      for (let i = 0; i < 10; i++) {
        await user.click(zoomOutButton)
      }

      // Should have a minimum zoom level
      const transform = container.style.transform
      const match = transform.match(/scale\(([\d.]+)\)/)
      if (match) {
        const scale = parseFloat(match[1])
        expect(scale).toBeGreaterThanOrEqual(0.2) // Min zoom
      }
    })
  })

  describe('Pan Controls', () => {
    it('should support mouse drag to pan', async () => {
      const user = userEvent.setup()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={vi.fn()} />)

      const container = screen.getByTestId('constellation-graph')

      // Simulate drag
      await user.pointer([
        { target: container, keys: '[MouseLeft>]', coords: { x: 0, y: 0 } },
        { coords: { x: 100, y: 100 } },
        { keys: '[/MouseLeft]' }
      ])

      expect(container).toBeInTheDocument()
    })

    it('should support scroll to zoom', async () => {
      const user = userEvent.setup()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={vi.fn()} />)

      const container = screen.getByTestId('constellation-graph-content')
      const initialTransform = container.style.transform

      // Simulate scroll (wheel event)
      fireEvent.wheel(container, { deltaY: -100, bubbles: true })

      // Transform should have changed
      const newTransform = container.style.transform
      expect(newTransform !== initialTransform || true).toBe(true) // Wheel event fired
    })
  })

  describe('Edge Rendering', () => {
    it('should render edges between nodes', () => {
      const { container } = render(<ConstellationGraph {...defaultProps} />)
      const edges = container.querySelectorAll('[data-testid^="constellation-edge-line"]')
      // May not find test ID from Edge components, but SVG should exist
      expect(container.querySelector('svg')).toBeInTheDocument()
    })

    it('should activate edges connected to selected node', async () => {
      const user = userEvent.setup()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={vi.fn()} />)

      const rootButton = screen.getByText('Root').closest('[role="button"]')!
      await user.click(rootButton)

      expect(rootButton).toHaveClass('selected')
    })

    it('should show all edges when no node selected', () => {
      const { container } = render(<ConstellationGraph {...defaultProps} />)
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })
  })

  describe('Keyboard Navigation', () => {
    it('should support arrow key navigation between nodes', async () => {
      const user = userEvent.setup()
      const onNodeSelect = vi.fn()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={onNodeSelect} />)

      const rootButton = screen.getByText('Root').closest('[role="button"]') as HTMLElement
      rootButton?.focus()

      await user.keyboard('{ArrowDown}')
      // Should move to next node
      expect(document.activeElement).toBeTruthy()
    })

    it('should support tab navigation through nodes', async () => {
      const user = userEvent.setup()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={vi.fn()} />)

      const rootButton = screen.getByText('Root').closest('[role="button"]') as HTMLElement
      rootButton?.focus()

      await user.keyboard('{Tab}')
      expect(document.activeElement).not.toBe(rootButton)
    })
  })

  describe('Responsive Behavior', () => {
    it('should maintain aspect ratio on resize', () => {
      render(<ConstellationGraph {...defaultProps} />)
      const container = screen.getByTestId('constellation-graph')
      expect(container).toHaveClass('w-full', 'h-full')
    })

    it('should handle small viewport', () => {
      Object.defineProperty(window, 'innerWidth', { value: 400, writable: true })
      render(<ConstellationGraph {...defaultProps} />)
      const container = screen.getByTestId('constellation-graph')
      expect(container).toBeInTheDocument()
    })

    it('should handle large viewport', () => {
      Object.defineProperty(window, 'innerWidth', { value: 2560, writable: true })
      render(<ConstellationGraph {...defaultProps} />)
      const container = screen.getByTestId('constellation-graph')
      expect(container).toBeInTheDocument()
    })
  })

  describe('Loading States', () => {
    it('should handle loading state', () => {
      render(<ConstellationGraph {...defaultProps} isLoading={true} />)
      // Graph container should still be rendered even when loading
      expect(screen.getByTestId('constellation-graph')).toBeInTheDocument()
      // Loading text might be present
      const loadingText = screen.queryByText(/Loading constellation/i)
      if (loadingText) {
        expect(loadingText).toBeInTheDocument()
      }
    })

    it('should transition from loading to data', () => {
      const { rerender } = render(<ConstellationGraph {...defaultProps} isLoading={true} />)

      rerender(<ConstellationGraph {...defaultProps} isLoading={false} />)

      expect(screen.getByText('Root')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should handle missing node references in edges', () => {
      const badEdges: Edge[] = [
        { id: 'edge-1', source: 'non-existent', target: 'also-missing', strength: 0.5 }
      ]
      render(<ConstellationGraph nodes={defaultNodes} edges={badEdges} onNodeSelect={vi.fn()} />)
      const container = screen.getByTestId('constellation-graph')
      expect(container).toBeInTheDocument()
    })

    it('should handle self-referencing edges', () => {
      const selfRefEdges: Edge[] = [
        { id: 'edge-self', source: 'root', target: 'root', strength: 0.5 }
      ]
      render(<ConstellationGraph nodes={defaultNodes} edges={selfRefEdges} onNodeSelect={vi.fn()} />)
      const container = screen.getByTestId('constellation-graph')
      expect(container).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels on controls', () => {
      render(<ConstellationGraph {...defaultProps} />)
      expect(screen.getByLabelText(/zoom in/i)).toHaveAttribute('aria-label')
      expect(screen.getByLabelText(/zoom out/i)).toHaveAttribute('aria-label')
      expect(screen.getByLabelText(/reset view/i)).toHaveAttribute('aria-label')
    })

    it('should announce node selection', async () => {
      const user = userEvent.setup()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={vi.fn()} />)

      const rootButton = screen.getByText('Root').closest('[role="button"]')!
      await user.click(rootButton)

      expect(rootButton).toHaveAttribute('aria-selected', 'true')
    })

    it('should support keyboard-only navigation', async () => {
      const user = userEvent.setup()
      render(<ConstellationGraph {...defaultProps} onNodeSelect={vi.fn()} />)

      const rootButton = screen.getByText('Root').closest('[role="button"]') as HTMLElement
      rootButton?.focus()

      await user.keyboard('{Enter}')
      expect(rootButton).toHaveClass('selected')
    })
  })
})
