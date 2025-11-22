/**
 * Test file
 *
 * @CODE:FRONTEND-001
 * @TEST:TAXONOMY-VIZ-001
 */

import { describe, it, expect, vi, beforeAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import { createRef } from 'react'
import TaxonomyNode from '../TaxonomyNode'
import type { NodeProps } from '@xyflow/react'
import type { TaxonomyNode as TaxonomyNodeData } from '../../../lib/api/types'

// Mock React Flow Handle component to avoid zustand provider errors
vi.mock('@xyflow/react', async () => {
  const actual = await vi.importActual('@xyflow/react')
  return {
    ...actual,
    Handle: ({ type, position }: { type: string; position: string }) => (
      <div data-testid={`handle-${type}-${position}`} />
    ),
  }
})

beforeAll(() => {
  // Mock console.error to suppress React Flow warnings in tests
  vi.spyOn(console, 'error').mockImplementation(() => {})
})

const mockNodeData: TaxonomyNodeData = {
  id: 'node-1',
  name: 'Technology',
  path: ['Root', 'Technology'],
  parent_id: 'root',
  level: 1,
  children: [],
}

const mockNodeProps: NodeProps = {
  id: 'node-1',
  data: {
    taxonomyNode: mockNodeData,
    isExpanded: true,
  },
  selected: false,
  type: 'custom',
  xPos: 0,
  yPos: 0,
  zIndex: 0,
  isConnectable: true,
  positionAbsoluteX: 0,
  positionAbsoluteY: 0,
  dragging: false,
}

describe('TaxonomyNode', () => {
  it('should render node with taxonomy name', () => {
    render(<TaxonomyNode {...mockNodeProps} />)
    expect(screen.getByText('Technology')).toBeInTheDocument()
  })

  it('should display node level', () => {
    render(<TaxonomyNode {...mockNodeProps} />)
    expect(screen.getByText(/level 1/i)).toBeInTheDocument()
  })

  it('should display document count when available', () => {
    const propsWithDocCount: NodeProps = {
      ...mockNodeProps,
      data: {
        ...mockNodeProps.data,
        taxonomyNode: {
          ...mockNodeData,
          document_count: 42,
        },
      },
    }
    render(<TaxonomyNode {...propsWithDocCount} />)
    expect(screen.getByText(/42/)).toBeInTheDocument()
  })

  it('should show 0 documents when document_count is missing', () => {
    render(<TaxonomyNode {...mockNodeProps} />)
    expect(screen.getByText(/0/)).toBeInTheDocument()
  })

  it('should apply selected styling when node is selected', () => {
    const selectedProps: NodeProps = {
      ...mockNodeProps,
      selected: true,
    }
    render(<TaxonomyNode {...selectedProps} />)
    const nodeElement = screen.getByRole('button', { name: /taxonomy node/i })
    expect(nodeElement).toHaveClass('ring-2', 'ring-blue-500')
  })

  it('should not apply selected styling when node is not selected', () => {
    render(<TaxonomyNode {...mockNodeProps} />)
    const nodeElement = screen.getByRole('button', { name: /taxonomy node/i })
    expect(nodeElement).not.toHaveClass('ring-2')
  })

  it('should truncate long node names with ellipsis', () => {
    const longNameProps: NodeProps = {
      ...mockNodeProps,
      data: {
        ...mockNodeProps.data,
        taxonomyNode: {
          ...mockNodeData,
          name: 'A very long taxonomy node name that exceeds fifty characters limit',
        },
      },
    }
    render(<TaxonomyNode {...longNameProps} />)
    const nameElement = screen.getByText(/A very long taxonomy node name/)
    expect(nameElement).toHaveClass('truncate')
  })

  it('should render with correct ARIA label for accessibility', () => {
    render(<TaxonomyNode {...mockNodeProps} />)
    const nodeElement = screen.getByLabelText(/taxonomy node: technology/i)
    expect(nodeElement).toBeInTheDocument()
  })

  it('should display children indicator when node has children', () => {
    const propsWithChildren: NodeProps = {
      ...mockNodeProps,
      data: {
        ...mockNodeProps.data,
        taxonomyNode: {
          ...mockNodeData,
          children: [
            {
              id: 'child-1',
              name: 'Child',
              path: ['Root', 'Technology', 'Child'],
              parent_id: 'node-1',
              level: 2,
              children: [],
            },
          ],
        },
      },
    }
    render(<TaxonomyNode {...propsWithChildren} />)
    expect(screen.getByTestId('children-indicator')).toBeInTheDocument()
  })

  it('should not display children indicator when node has no children', () => {
    render(<TaxonomyNode {...mockNodeProps} />)
    expect(screen.queryByTestId('children-indicator')).not.toBeInTheDocument()
  })

  // TAG-003: Focus management tests
  describe('Focus Management (TAG-003)', () => {
    it('should accept ref and forward it to the node element', () => {
      const ref = createRef<HTMLDivElement>()
      render(<TaxonomyNode {...mockNodeProps} ref={ref} />)

      expect(ref.current).not.toBeNull()
      expect(ref.current?.tagName).toBe('DIV')
      expect(ref.current?.getAttribute('role')).toBe('button')
    })

    it('should allow programmatic focus via ref', () => {
      const ref = createRef<HTMLDivElement>()
      render(<TaxonomyNode {...mockNodeProps} ref={ref} />)

      ref.current?.focus()
      expect(ref.current).toBe(document.activeElement)
    })

    it('should apply focus-visible styles when focused', () => {
      const ref = createRef<HTMLDivElement>()
      render(<TaxonomyNode {...mockNodeProps} ref={ref} />)

      ref.current?.focus()
      expect(ref.current).toHaveClass('focus-visible:outline-blue-500')
    })

    it('should maintain tabIndex={0} for keyboard accessibility', () => {
      render(<TaxonomyNode {...mockNodeProps} />)
      const nodeElement = screen.getByRole('button', { name: /taxonomy node/i })
      expect(nodeElement).toHaveAttribute('tabIndex', '0')
    })
  })
})
