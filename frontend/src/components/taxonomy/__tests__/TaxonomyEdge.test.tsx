/**
 * Test file
 *
 * @CODE:FRONTEND-001
 * @TEST:TAXONOMY-VIZ-001
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import TaxonomyEdge from '../TaxonomyEdge'
import type { EdgeProps } from '@xyflow/react'

const mockEdgeProps: EdgeProps = {
  id: 'edge-1',
  source: 'node-1',
  target: 'node-2',
  sourceX: 100,
  sourceY: 100,
  targetX: 200,
  targetY: 200,
  sourcePosition: 'bottom' as const,
  targetPosition: 'top' as const,
  selected: false,
  animated: false,
  data: {},
}

describe('TaxonomyEdge', () => {
  it('should render SVG path element', () => {
    const { container } = render(<TaxonomyEdge {...mockEdgeProps} />)
    const pathElement = container.querySelector('path')
    expect(pathElement).toBeInTheDocument()
  })

  it('should apply default stroke color', () => {
    const { container } = render(<TaxonomyEdge {...mockEdgeProps} />)
    const pathElement = container.querySelector('path')
    expect(pathElement).toHaveAttribute('stroke', '#b1b1b7')
  })

  it('should apply selected stroke color when edge is selected', () => {
    const selectedProps: EdgeProps = {
      ...mockEdgeProps,
      selected: true,
    }
    const { container } = render(<TaxonomyEdge {...selectedProps} />)
    const pathElement = container.querySelector('path')
    expect(pathElement).toHaveAttribute('stroke', '#3b82f6')
  })

  it('should have correct stroke width', () => {
    const { container } = render(<TaxonomyEdge {...mockEdgeProps} />)
    const pathElement = container.querySelector('path')
    expect(pathElement).toHaveAttribute('stroke-width', '2')
  })

  it('should have rounded line caps', () => {
    const { container } = render(<TaxonomyEdge {...mockEdgeProps} />)
    const pathElement = container.querySelector('path')
    expect(pathElement).toHaveAttribute('stroke-linecap', 'round')
  })

  it('should render with correct ARIA label', () => {
    render(<TaxonomyEdge {...mockEdgeProps} />)
    const edgeElement = screen.getByLabelText(/edge from node-1 to node-2/i)
    expect(edgeElement).toBeInTheDocument()
  })

  it('should render marker-end for arrow indicator', () => {
    const { container } = render(<TaxonomyEdge {...mockEdgeProps} />)
    const pathElement = container.querySelector('path')
    expect(pathElement).toHaveAttribute('marker-end')
  })

  it('should animate when animated prop is true', () => {
    const animatedProps: EdgeProps = {
      ...mockEdgeProps,
      animated: true,
    }
    const { container } = render(<TaxonomyEdge {...animatedProps} />)
    const pathElement = container.querySelector('path')
    expect(pathElement).toHaveClass('animated')
  })
})
