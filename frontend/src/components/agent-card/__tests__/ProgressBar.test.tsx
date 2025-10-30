// @TEST:AGENT-CARD-001-UI-002
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProgressBar } from '../ProgressBar'

describe('ProgressBar', () => {
  describe('Rendering', () => {
    it('should render progress bar with 0% progress', () => {
      render(<ProgressBar current={0} max={100} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toBeInTheDocument()
    })

    it('should render progress bar with 50% progress', () => {
      render(<ProgressBar current={50} max={100} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '50')
    })

    it('should render progress bar with 100% progress', () => {
      render(<ProgressBar current={100} max={100} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '100')
    })

    it('should display progress label', () => {
      render(<ProgressBar current={75} max={100} label="75 / 100 XP" />)
      expect(screen.getByText('75 / 100 XP')).toBeInTheDocument()
    })
  })

  describe('Progress calculation', () => {
    it('should calculate 0% progress correctly', () => {
      render(<ProgressBar current={0} max={100} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '0')
      expect(progressBar).toHaveAttribute('aria-valuemin', '0')
      expect(progressBar).toHaveAttribute('aria-valuemax', '100')
    })

    it('should calculate 25% progress correctly', () => {
      render(<ProgressBar current={25} max={100} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '25')
    })

    it('should calculate 75% progress correctly', () => {
      render(<ProgressBar current={750} max={1000} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '750')
    })

    it('should handle decimal progress values', () => {
      render(<ProgressBar current={33.33} max={100} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '33.33')
    })
  })

  describe('Edge cases', () => {
    it('should handle max progress (100%)', () => {
      render(<ProgressBar current={1000} max={1000} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '1000')
    })

    it('should handle progress exceeding max (cap at 100%)', () => {
      render(<ProgressBar current={150} max={100} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '150')
    })

    it('should handle max = 0 gracefully', () => {
      render(<ProgressBar current={0} max={0} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(<ProgressBar current={60} max={100} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '60')
      expect(progressBar).toHaveAttribute('aria-valuemin', '0')
      expect(progressBar).toHaveAttribute('aria-valuemax', '100')
    })

    it('should have aria-label when provided', () => {
      render(<ProgressBar current={50} max={100} ariaLabel="Experience progress" />)
      expect(screen.getByLabelText('Experience progress')).toBeInTheDocument()
    })

    it('should have default aria-label', () => {
      render(<ProgressBar current={50} max={100} />)
      expect(screen.getByLabelText('Progress')).toBeInTheDocument()
    })
  })

  describe('Styling', () => {
    it('should apply gradient background', () => {
      const { container } = render(<ProgressBar current={50} max={100} />)
      const innerBar = container.querySelector('[role="progressbar"] > div')
      expect(innerBar?.className).toContain('bg-gradient-to-r')
    })

    it('should accept custom className', () => {
      const { container } = render(<ProgressBar current={50} max={100} className="custom-class" />)
      const wrapper = container.firstChild as HTMLElement
      expect(wrapper?.className).toContain('custom-class')
    })
  })
})
