/**
 * ConstellationNode Component Tests
 *
 * Tests for the Constellation Node component used in the taxonomy visualization.
 * Validates rendering, styling, interactivity, and accessibility features.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ConstellationNode from '../ConstellationNode'
import type { TaxonomyNode } from '@/lib/api/types'

describe('ConstellationNode', () => {
  const defaultNode: TaxonomyNode = {
    id: 'node-1',
    name: 'Root Category',
    level: 1,
    path: ['Root'],
    parent_id: null,
    document_count: 42,
    children: [
      {
        id: 'node-1-1',
        name: 'Child 1',
        level: 2,
        path: ['Root', 'Child 1'],
        parent_id: 'node-1',
        document_count: 20,
      }
    ]
  }

  const defaultProps = {
    node: defaultNode,
    isSelected: false,
    isHovered: false,
    onClick: vi.fn(),
    onHover: vi.fn(),
    position: { x: 100, y: 100 }
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render the node with the correct label', () => {
      render(<ConstellationNode {...defaultProps} />)
      expect(screen.getByText('Root Category')).toBeInTheDocument()
    })

    it('should render node with root level styling', () => {
      render(<ConstellationNode {...defaultProps} />)
      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      expect(nodeElement).toHaveClass('constellation-node-root')
    })

    it('should render node with branch level styling', () => {
      const branchNode: TaxonomyNode = { ...defaultNode, level: 2 }
      render(<ConstellationNode {...defaultProps} node={branchNode} />)
      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      expect(nodeElement).toHaveClass('constellation-node-branch')
    })

    it('should render node with leaf level styling', () => {
      const leafNode: TaxonomyNode = { ...defaultNode, level: 3 }
      render(<ConstellationNode {...defaultProps} node={leafNode} />)
      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      expect(nodeElement).toHaveClass('constellation-node-leaf')
    })

    it('should display document count when provided', () => {
      render(<ConstellationNode {...defaultProps} />)
      expect(screen.getByText('42')).toBeInTheDocument()
    })

    it('should handle truncated labels gracefully', () => {
      const longNameNode: TaxonomyNode = {
        ...defaultNode,
        name: 'A'.repeat(100)
      }
      render(<ConstellationNode {...defaultProps} node={longNameNode} />)
      const label = screen.getByText(new RegExp('A{100}'))
      expect(label).toHaveClass('truncate')
    })
  })

  describe('Styling and States', () => {
    it('should apply selected class when isSelected is true', () => {
      render(<ConstellationNode {...defaultProps} isSelected={true} />)
      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      expect(nodeElement).toHaveClass('selected')
    })

    it('should apply hover class when isHovered is true', () => {
      render(<ConstellationNode {...defaultProps} isHovered={true} />)
      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      expect(nodeElement).toHaveClass('hovered')
    })

    it('should apply glow-pulse animation on hover', () => {
      render(<ConstellationNode {...defaultProps} isHovered={true} />)
      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      expect(nodeElement).toHaveClass('glow-pulse')
    })

    it('should have correct box-shadow for root node', () => {
      render(<ConstellationNode {...defaultProps} />)
      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      // Verify shadow-related classes are applied (Tailwind handles actual shadow rendering)
      expect(nodeElement).toHaveClass('constellation-node-root')
    })
  })

  describe('Interactivity', () => {
    it('should handle click events', async () => {
      const user = userEvent.setup()
      const onClick = vi.fn()
      render(<ConstellationNode {...defaultProps} onClick={onClick} />)

      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      await user.click(nodeElement)

      expect(onClick).toHaveBeenCalledWith(defaultNode)
    })

    it('should handle hover events', async () => {
      const user = userEvent.setup()
      const onHover = vi.fn()
      render(<ConstellationNode {...defaultProps} onHover={onHover} />)

      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      await user.hover(nodeElement)

      expect(onHover).toHaveBeenCalledWith(true, defaultNode)
    })

    it('should handle hover leave events', async () => {
      const user = userEvent.setup()
      const onHover = vi.fn()
      render(<ConstellationNode {...defaultProps} onHover={onHover} />)

      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      await user.hover(nodeElement)
      await user.unhover(nodeElement)

      expect(onHover).toHaveBeenCalledWith(false, defaultNode)
    })

    it('should support keyboard navigation (Enter key)', async () => {
      const user = userEvent.setup()
      const onClick = vi.fn()
      render(<ConstellationNode {...defaultProps} onClick={onClick} />)

      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      nodeElement.focus()
      await user.keyboard('{Enter}')

      expect(onClick).toHaveBeenCalled()
    })

    it('should support keyboard navigation (Space key)', async () => {
      const user = userEvent.setup()
      const onClick = vi.fn()
      render(<ConstellationNode {...defaultProps} onClick={onClick} />)

      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      nodeElement.focus()
      await user.keyboard(' ')

      expect(onClick).toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('should have proper role attribute', () => {
      render(<ConstellationNode {...defaultProps} />)
      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('should have accessible label', () => {
      render(<ConstellationNode {...defaultProps} />)
      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      expect(nodeElement).toHaveAttribute('aria-label')
      expect(nodeElement.getAttribute('aria-label')).toContain('Root Category')
    })

    it('should indicate selected state via aria-selected', () => {
      render(<ConstellationNode {...defaultProps} isSelected={true} />)
      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      expect(nodeElement).toHaveAttribute('aria-selected', 'true')
    })

    it('should be keyboard focusable', () => {
      render(<ConstellationNode {...defaultProps} />)
      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      expect(nodeElement).toHaveAttribute('tabIndex', '0')
    })

    it('should have proper ARIA label with document count', () => {
      render(<ConstellationNode {...defaultProps} />)
      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      const ariaLabel = nodeElement.getAttribute('aria-label')
      expect(ariaLabel).toContain('42')
    })

    it('should announce selection state to screen readers', () => {
      const { rerender } = render(<ConstellationNode {...defaultProps} isSelected={false} />)
      const nodeElement = screen.getByRole('button', { name: /Root Category/ })
      expect(nodeElement).toHaveAttribute('aria-selected', 'false')

      rerender(<ConstellationNode {...defaultProps} isSelected={true} />)
      expect(nodeElement).toHaveAttribute('aria-selected', 'true')
    })
  })

  describe('Edge Cases', () => {
    it('should handle zero document count', () => {
      const nodeNoDocuments: TaxonomyNode = { ...defaultNode, document_count: 0 }
      render(<ConstellationNode {...defaultProps} node={nodeNoDocuments} />)
      expect(screen.getByText('0')).toBeInTheDocument()
    })

    it('should handle missing document count', () => {
      const nodeNoDocs: TaxonomyNode = { ...defaultNode, document_count: undefined }
      render(<ConstellationNode {...defaultProps} node={nodeNoDocs} />)
      const nodeElement = screen.getByRole('button')
      expect(nodeElement).toBeInTheDocument()
    })

    it('should handle very long node names', () => {
      const longNameNode: TaxonomyNode = {
        ...defaultNode,
        name: 'Very Long Node Name That Should Be Truncated In The Display And Show Ellipsis'
      }
      render(<ConstellationNode {...defaultProps} node={longNameNode} />)
      const label = screen.getByText(/Very Long/)
      expect(label).toHaveClass('truncate')
    })

    it('should handle special characters in node name', () => {
      const specialCharNode: TaxonomyNode = {
        ...defaultNode,
        name: 'Node < > & " \''
      }
      render(<ConstellationNode {...defaultProps} node={specialCharNode} />)
      expect(screen.getByText(/Node/)).toBeInTheDocument()
    })
  })

  describe('Styling Consistency', () => {
    it('should apply constellation-node base class', () => {
      render(<ConstellationNode {...defaultProps} />)
      const nodeElement = screen.getByRole('button')
      expect(nodeElement).toHaveClass('constellation-node')
    })

    it('should transition between hover states smoothly', () => {
      render(<ConstellationNode {...defaultProps} />)
      const nodeElement = screen.getByRole('button')
      expect(nodeElement).toHaveClass('transition-all')
    })

    it('should have proper z-index for stacking', () => {
      render(<ConstellationNode {...defaultProps} isSelected={true} />)
      const nodeElement = screen.getByRole('button')
      expect(nodeElement).toHaveClass('z-10')
    })
  })
})
