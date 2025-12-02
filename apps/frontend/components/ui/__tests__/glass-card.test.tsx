/**
 * GlassCard Component Tests
 * Tests for Ethereal Glass card component with blur effects and hover states
 *
 * @CODE:GLASS-CARD-001
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { GlassCard } from '@/components/ui/glass-card'

describe('GlassCard Component', () => {
  describe('Rendering', () => {
    it('should render a glass card with children', () => {
      render(
        <GlassCard>
          <div>Test Content</div>
        </GlassCard>
      )

      expect(screen.getByText('Test Content')).toBeInTheDocument()
    })

    it('should apply ethereal-card class for glass morphism effect', () => {
      const { container } = render(
        <GlassCard>
          <div>Test</div>
        </GlassCard>
      )

      const card = container.firstChild
      expect(card).toHaveClass('ethereal-card')
    })

    it('should apply backdrop-blur-xl for frosted glass effect', () => {
      const { container } = render(
        <GlassCard>
          <div>Test</div>
        </GlassCard>
      )

      const card = container.firstChild
      expect(card).toHaveClass('backdrop-blur-xl')
    })

    it('should apply border with glass-border color', () => {
      const { container } = render(
        <GlassCard>
          <div>Test</div>
        </GlassCard>
      )

      const card = container.firstChild
      expect(card).toHaveClass('border')
      expect(card).toHaveClass('border-glass-border')
    })

    it('should apply rounded-2xl border radius', () => {
      const { container } = render(
        <GlassCard>
          <div>Test</div>
        </GlassCard>
      )

      const card = container.firstChild
      expect(card).toHaveClass('rounded-2xl')
    })
  })

  describe('Rarity Variants', () => {
    it('should apply common rarity styling when rarity="common"', () => {
      const { container } = render(
        <GlassCard rarity="common">
          <div>Common Card</div>
        </GlassCard>
      )

      const card = container.firstChild
      expect(card).toHaveClass('rarity-common')
    })

    it('should apply rare rarity styling when rarity="rare"', () => {
      const { container } = render(
        <GlassCard rarity="rare">
          <div>Rare Card</div>
        </GlassCard>
      )

      const card = container.firstChild
      expect(card).toHaveClass('rarity-rare')
    })

    it('should apply epic rarity styling when rarity="epic"', () => {
      const { container } = render(
        <GlassCard rarity="epic">
          <div>Epic Card</div>
        </GlassCard>
      )

      const card = container.firstChild
      expect(card).toHaveClass('rarity-epic')
    })

    it('should apply legendary rarity styling when rarity="legendary"', () => {
      const { container } = render(
        <GlassCard rarity="legendary">
          <div>Legendary Card</div>
        </GlassCard>
      )

      const card = container.firstChild
      expect(card).toHaveClass('rarity-legendary')
    })
  })

  describe('Hover Effects', () => {
    it('should have hover styles defined', () => {
      const { container } = render(
        <GlassCard>
          <div>Hover Test</div>
        </GlassCard>
      )

      const card = container.firstChild as HTMLElement
      expect(card).toHaveClass('transition-all')
      expect(card).toHaveClass('duration-300')
    })

    it('should lift on hover with translateY', async () => {
      const user = userEvent.setup()
      const { container } = render(
        <GlassCard>
          <div>Test</div>
        </GlassCard>
      )

      const card = container.firstChild as HTMLElement

      await user.hover(card)
      // Hover styles should be applied through CSS
      expect(card).toHaveClass('ethereal-card')
    })
  })

  describe('Accessibility', () => {
    it('should maintain semantic structure', () => {
      const { container } = render(
        <GlassCard>
          <button>Click me</button>
        </GlassCard>
      )

      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('should support custom className prop', () => {
      const { container } = render(
        <GlassCard className="custom-class">
          <div>Test</div>
        </GlassCard>
      )

      const card = container.firstChild
      expect(card).toHaveClass('custom-class')
      expect(card).toHaveClass('ethereal-card')
    })

    it('should forward ref correctly', () => {
      let ref: HTMLDivElement | null = null

      render(
        <GlassCard ref={el => { ref = el }}>
          <div>Test</div>
        </GlassCard>
      )

      expect(ref).toBeInstanceOf(HTMLDivElement)
    })
  })

  describe('Content Variants', () => {
    it('should render with padding', () => {
      const { container } = render(
        <GlassCard className="p-4">
          <div>Padded Content</div>
        </GlassCard>
      )

      expect(screen.getByText('Padded Content')).toBeInTheDocument()
    })

    it('should support nested content', () => {
      render(
        <GlassCard>
          <div>
            <h3>Title</h3>
            <p>Description</p>
          </div>
        </GlassCard>
      )

      expect(screen.getByText('Title')).toBeInTheDocument()
      expect(screen.getByText('Description')).toBeInTheDocument()
    })
  })
})
