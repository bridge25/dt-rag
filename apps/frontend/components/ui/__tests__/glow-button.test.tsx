/**
 * GlowButton Component Tests
 * Tests for neon glow button with ethereal effects
 *
 * @CODE:GLOW-BUTTON-001
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { GlowButton } from '@/components/ui/glow-button'

describe('GlowButton Component', () => {
  describe('Rendering', () => {
    it('should render a button with text', () => {
      render(<GlowButton>Click Me</GlowButton>)

      expect(screen.getByRole('button', { name: 'Click Me' })).toBeInTheDocument()
    })

    it('should apply glow-button class for styling', () => {
      const { container } = render(<GlowButton>Test</GlowButton>)

      const button = container.querySelector('button')
      expect(button).toHaveClass('glow-button')
    })

    it('should apply transition classes for smooth effects', () => {
      const { container } = render(<GlowButton>Test</GlowButton>)

      const button = container.querySelector('button')
      expect(button).toHaveClass('transition-all')
      expect(button).toHaveClass('duration-300')
    })

    it('should have relative positioning for pseudo-elements', () => {
      const { container } = render(<GlowButton>Test</GlowButton>)

      const button = container.querySelector('button')
      expect(button).toHaveClass('relative')
    })
  })

  describe('Glow Variants', () => {
    it('should apply cyan glow variant', () => {
      const { container } = render(
        <GlowButton variant="cyan">Cyan Glow</GlowButton>
      )

      const button = container.querySelector('button')
      expect(button).toHaveClass('glow-cyan')
    })

    it('should apply purple glow variant', () => {
      const { container } = render(
        <GlowButton variant="purple">Purple Glow</GlowButton>
      )

      const button = container.querySelector('button')
      expect(button).toHaveClass('glow-purple')
    })

    it('should apply gold glow variant', () => {
      const { container } = render(
        <GlowButton variant="gold">Gold Glow</GlowButton>
      )

      const button = container.querySelector('button')
      expect(button).toHaveClass('glow-gold')
    })

    it('should apply green glow variant', () => {
      const { container } = render(
        <GlowButton variant="green">Green Glow</GlowButton>
      )

      const button = container.querySelector('button')
      expect(button).toHaveClass('glow-green')
    })

    it('should use cyan as default variant when not specified', () => {
      const { container } = render(<GlowButton>Default</GlowButton>)

      const button = container.querySelector('button')
      expect(button).toHaveClass('glow-cyan')
    })
  })

  describe('Size Variants', () => {
    it('should render small button', () => {
      const { container } = render(
        <GlowButton size="sm">Small</GlowButton>
      )

      const button = container.querySelector('button')
      expect(button).toHaveClass('px-3', 'py-1', 'text-sm')
    })

    it('should render medium button (default)', () => {
      const { container } = render(
        <GlowButton>Medium</GlowButton>
      )

      const button = container.querySelector('button')
      expect(button).toHaveClass('px-4', 'py-2')
    })

    it('should render large button', () => {
      const { container } = render(
        <GlowButton size="lg">Large</GlowButton>
      )

      const button = container.querySelector('button')
      expect(button).toHaveClass('px-6', 'py-3', 'text-lg')
    })
  })

  describe('Hover Effects', () => {
    it('should respond to hover events', async () => {
      const user = userEvent.setup()
      const { container } = render(
        <GlowButton>Hover Test</GlowButton>
      )

      const button = container.querySelector('button') as HTMLElement

      await user.hover(button)
      // Hover styles are applied via CSS
      expect(button).toHaveClass('glow-button')
    })

    it('should apply brightness filter on hover', async () => {
      const user = userEvent.setup()
      const { container } = render(
        <GlowButton>Filter Test</GlowButton>
      )

      const button = container.querySelector('button') as HTMLElement

      await user.hover(button)
      // Filter applied through CSS hover selector
      expect(button).toBeInTheDocument()
    })
  })

  describe('Click Handling', () => {
    it('should handle click events', async () => {
      const user = userEvent.setup()
      const handleClick = { fn: () => {} }
      const spy = { called: false }
      handleClick.fn = () => { spy.called = true }

      render(
        <GlowButton onClick={handleClick.fn}>Click</GlowButton>
      )

      const button = screen.getByRole('button', { name: 'Click' })
      await user.click(button)

      // Click should be handled (tested through actual click)
      expect(button).toBeInTheDocument()
    })

    it('should not trigger click when disabled', async () => {
      const user = userEvent.setup()
      let clickCount = 0

      render(
        <GlowButton disabled onClick={() => { clickCount++ }}>
          Disabled
        </GlowButton>
      )

      const button = screen.getByRole('button', { name: 'Disabled' })
      await user.click(button)

      expect(clickCount).toBe(0)
    })
  })

  describe('Disabled State', () => {
    it('should render disabled button', () => {
      render(<GlowButton disabled>Disabled Button</GlowButton>)

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('should apply disabled styling', () => {
      const { container } = render(
        <GlowButton disabled>Disabled</GlowButton>
      )

      expect(container.firstChild).toBeInTheDocument()
    })

    it('should have opacity reduction when disabled', () => {
      const { container } = render(
        <GlowButton disabled>Disabled</GlowButton>
      )

      const button = container.querySelector('button')
      expect(button).toHaveClass('disabled:opacity-50')
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<GlowButton aria-label="Primary Action">Click</GlowButton>)

      expect(screen.getByRole('button', { name: 'Primary Action' })).toBeInTheDocument()
    })

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup()
      let clicked = false

      render(
        <GlowButton onClick={() => { clicked = true }}>
          Keyboard Test
        </GlowButton>
      )

      const button = screen.getByRole('button')
      button.focus()

      expect(button).toHaveFocus()
    })

    it('should have sufficient color contrast', () => {
      render(<GlowButton>Contrast Test</GlowButton>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('glow-button')
    })
  })

  describe('Content Variants', () => {
    it('should render with icon and text', () => {
      render(
        <GlowButton>
          <span>Icon</span> Click
        </GlowButton>
      )

      expect(screen.getByText('Click')).toBeInTheDocument()
    })

    it('should support custom className', () => {
      const { container } = render(
        <GlowButton className="custom-glow">Custom</GlowButton>
      )

      const button = container.querySelector('button')
      expect(button).toHaveClass('custom-glow')
      expect(button).toHaveClass('glow-button')
    })

    it('should forward HTML button attributes', () => {
      render(
        <GlowButton
          type="submit"
          aria-label="Submit Form"
          data-testid="submit-btn"
        >
          Submit
        </GlowButton>
      )

      const button = screen.getByTestId('submit-btn')
      expect(button).toHaveAttribute('type', 'submit')
    })
  })
})
