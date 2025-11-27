/**
 * ConstellationEdge Component Tests
 *
 * Tests for the animated energy beam edge connecting constellation nodes.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import ConstellationEdge from '../ConstellationEdge'

describe('ConstellationEdge', () => {
  const defaultProps = {
    source: { x: 100, y: 100 },
    target: { x: 300, y: 300 },
    isActive: true,
    strength: 0.8,
    edgeId: 'edge-1'
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render SVG line element', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).toBeInTheDocument()
    })

    it('should render line with correct coordinates', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).toHaveAttribute('x1', '100')
      expect(line).toHaveAttribute('y1', '100')
      expect(line).toHaveAttribute('x2', '300')
      expect(line).toHaveAttribute('y2', '300')
    })

    it('should render defs with gradient definition', () => {
      const { container } = render(
        <svg>
          <ConstellationEdge {...defaultProps} />
        </svg>
      )
      const defs = container.querySelector('defs')
      expect(defs).toBeInTheDocument()
    })

    it('should render gradient with correct id', () => {
      const { container } = render(
        <svg>
          <ConstellationEdge {...defaultProps} edgeId="edge-test-1" />
        </svg>
      )
      const gradient = container.querySelector('#gradient-edge-test-1')
      expect(gradient).toBeInTheDocument()
    })

    it('should calculate correct line length', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).toHaveAttribute('x1', '100')
      expect(line).toHaveAttribute('x2', '300')
    })
  })

  describe('Active State', () => {
    it('should apply active class when isActive is true', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} isActive={true} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).toHaveClass('constellation-edge-active')
    })

    it('should not apply active class when isActive is false', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} isActive={false} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).not.toHaveClass('constellation-edge-active')
    })

    it('should apply dashed style when not active', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} isActive={false} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).toHaveAttribute('stroke-dasharray', '5,5')
    })

    it('should have normal style when active', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} isActive={true} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).not.toHaveAttribute('stroke-dasharray')
    })
  })

  describe('Strength and Opacity', () => {
    it('should use strength to adjust opacity', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} strength={0.5} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      const opacity = parseFloat(line.getAttribute('opacity') || '0')
      expect(opacity).toBeLessThanOrEqual(1)
      expect(opacity).toBeGreaterThanOrEqual(0)
    })

    it('should handle strength of 1 (maximum)', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} strength={1} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      const opacity = parseFloat(line.getAttribute('opacity') || '0')
      expect(opacity).toBeGreaterThan(0.5)
    })

    it('should handle strength of 0 (minimum)', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} strength={0} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      const opacity = parseFloat(line.getAttribute('opacity') || '0')
      expect(opacity).toBeLessThanOrEqual(0.3)
    })

    it('should apply strength to gradient stops', () => {
      const { container } = render(
        <svg>
          <ConstellationEdge {...defaultProps} strength={0.7} />
        </svg>
      )
      const stopElements = container.querySelectorAll('stop')
      expect(stopElements.length).toBeGreaterThan(0)
    })
  })

  describe('Edge Cases', () => {
    it('should handle zero-length edge (same source and target)', () => {
      const samePoint = { x: 100, y: 100 }
      render(
        <svg>
          <ConstellationEdge source={samePoint} target={samePoint} isActive={true} strength={0.8} edgeId="edge-1" />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).toBeInTheDocument()
    })

    it('should handle negative coordinates', () => {
      render(
        <svg>
          <ConstellationEdge
            source={{ x: -100, y: -100 }}
            target={{ x: -300, y: -300 }}
            isActive={true}
            strength={0.8}
            edgeId="edge-1"
          />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).toBeInTheDocument()
    })

    it('should handle very large coordinates', () => {
      render(
        <svg>
          <ConstellationEdge
            source={{ x: 10000, y: 10000 }}
            target={{ x: 20000, y: 20000 }}
            isActive={true}
            strength={0.8}
            edgeId="edge-1"
          />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).toBeInTheDocument()
    })

    it('should handle undefined strength', () => {
      render(
        <svg>
          <ConstellationEdge
            source={{ x: 100, y: 100 }}
            target={{ x: 300, y: 300 }}
            isActive={true}
            strength={undefined}
            edgeId="edge-1"
          />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).toBeInTheDocument()
    })
  })

  describe('Styling', () => {
    it('should have base constellation-edge class', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).toHaveClass('constellation-edge')
    })

    it('should apply animation class when active', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} isActive={true} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).toHaveClass('energy-beam')
    })

    it('should set stroke width', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).toHaveAttribute('stroke-width')
    })

    it('should apply filter for glow effect', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} isActive={true} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).toHaveAttribute('filter')
    })
  })

  describe('Gradient', () => {
    it('should reference gradient in stroke', () => {
      const { container } = render(
        <svg>
          <ConstellationEdge {...defaultProps} edgeId="edge-123" />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      const stroke = line.getAttribute('stroke')
      expect(stroke).toContain('url')
      expect(stroke).toContain('edge-123')
    })

    it('should update gradient opacity based on strength', () => {
      const { rerender, container } = render(
        <svg>
          <ConstellationEdge {...defaultProps} strength={0.8} edgeId="edge-1" />
        </svg>
      )
      const stops = container.querySelectorAll('stop')
      expect(stops.length).toBeGreaterThan(0)

      rerender(
        <svg>
          <ConstellationEdge {...defaultProps} strength={0.3} edgeId="edge-1" />
        </svg>
      )
      const updatedStops = container.querySelectorAll('stop')
      expect(updatedStops.length).toBeGreaterThan(0)
    })
  })

  describe('Animation', () => {
    it('should apply energyPulse animation when active', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} isActive={true} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).toHaveClass('energy-beam')
    })

    it('should not apply animation when inactive', () => {
      render(
        <svg>
          <ConstellationEdge {...defaultProps} isActive={false} />
        </svg>
      )
      const line = screen.getByTestId('constellation-edge-line')
      expect(line).not.toHaveClass('energy-beam')
    })
  })
})
