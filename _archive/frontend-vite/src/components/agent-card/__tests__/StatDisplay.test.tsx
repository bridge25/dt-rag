/**
 * Test file
 *
 * @CODE:FRONTEND-001
 * @TEST:AGENT-CARD-001
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatDisplay } from '../StatDisplay'

describe('StatDisplay', () => {
  describe('Rendering', () => {
    it('should render stat label and value', () => {
      render(<StatDisplay label="Documents" value={150} />)
      expect(screen.getByText('Documents')).toBeInTheDocument()
      expect(screen.getByText('150')).toBeInTheDocument()
    })

    it('should render with string value', () => {
      render(<StatDisplay label="Status" value="Active" />)
      expect(screen.getByText('Status')).toBeInTheDocument()
      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    it('should render with zero value', () => {
      render(<StatDisplay label="Queries" value={0} />)
      expect(screen.getByText('0')).toBeInTheDocument()
    })
  })

  describe('Icons', () => {
    it('should render with icon when provided', () => {
      const TestIcon = () => <svg data-testid="test-icon" />
      render(<StatDisplay label="Test" value={42} icon={<TestIcon />} />)
      expect(screen.getByTestId('test-icon')).toBeInTheDocument()
    })

    it('should render without icon when not provided', () => {
      const { container } = render(<StatDisplay label="Test" value={42} />)
      const svg = container.querySelector('svg')
      expect(svg).toBeNull()
    })
  })

  describe('Styling variants', () => {
    it('should apply default variant styling', () => {
      const { container } = render(<StatDisplay label="Test" value={100} />)
      const statDisplay = container.firstChild as HTMLElement
      expect(statDisplay).toBeInTheDocument()
    })

    it('should apply primary variant styling', () => {
      render(<StatDisplay label="Test" value={100} variant="primary" />)
      const valueElement = screen.getByText('100')
      expect(valueElement.className).toContain('text-primary')
    })

    it('should apply success variant styling', () => {
      render(<StatDisplay label="Test" value={100} variant="success" />)
      const valueElement = screen.getByText('100')
      expect(valueElement.className).toContain('text-green')
    })

    it('should apply warning variant styling', () => {
      render(<StatDisplay label="Test" value={100} variant="warning" />)
      const valueElement = screen.getByText('100')
      expect(valueElement.className).toContain('text-yellow')
    })
  })

  describe('Layout', () => {
    it('should render in vertical layout by default', () => {
      const { container } = render(<StatDisplay label="Test" value={100} />)
      const statDisplay = container.firstChild as HTMLElement
      expect(statDisplay.className).toContain('flex-col')
    })

    it('should render in horizontal layout when specified', () => {
      const { container } = render(<StatDisplay label="Test" value={100} layout="horizontal" />)
      const statDisplay = container.firstChild as HTMLElement
      expect(statDisplay.className).toContain('flex-row')
    })
  })

  describe('Custom className', () => {
    it('should accept and apply custom className', () => {
      const { container } = render(<StatDisplay label="Test" value={100} className="custom-stat" />)
      const statDisplay = container.firstChild as HTMLElement
      expect(statDisplay.className).toContain('custom-stat')
    })
  })

  describe('Accessibility', () => {
    it('should have proper semantic structure', () => {
      render(<StatDisplay label="Total Queries" value={250} />)
      expect(screen.getByText('Total Queries')).toBeInTheDocument()
      expect(screen.getByText('250')).toBeInTheDocument()
    })
  })
})
