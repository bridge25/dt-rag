// @TEST:AGENT-CARD-001-UI-001
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RarityBadge } from '../RarityBadge'
import type { Rarity } from '@/lib/api/types'

describe('RarityBadge', () => {
  describe('Rendering', () => {
    it('should render Common rarity badge', () => {
      render(<RarityBadge rarity="Common" />)
      expect(screen.getByText('Common')).toBeInTheDocument()
    })

    it('should render Rare rarity badge', () => {
      render(<RarityBadge rarity="Rare" />)
      expect(screen.getByText('Rare')).toBeInTheDocument()
    })

    it('should render Epic rarity badge', () => {
      render(<RarityBadge rarity="Epic" />)
      expect(screen.getByText('Epic')).toBeInTheDocument()
    })

    it('should render Legendary rarity badge', () => {
      render(<RarityBadge rarity="Legendary" />)
      expect(screen.getByText('Legendary')).toBeInTheDocument()
    })
  })

  describe('Styling', () => {
    it('should apply Common styling', () => {
      const { container } = render(<RarityBadge rarity="Common" />)
      const badge = container.firstChild as HTMLElement
      expect(badge.className).toContain('bg-gray')
    })

    it('should apply Rare styling', () => {
      const { container } = render(<RarityBadge rarity="Rare" />)
      const badge = container.firstChild as HTMLElement
      expect(badge.className).toContain('bg-blue')
    })

    it('should apply Epic styling', () => {
      const { container } = render(<RarityBadge rarity="Epic" />)
      const badge = container.firstChild as HTMLElement
      expect(badge.className).toContain('bg-purple')
    })

    it('should apply Legendary styling', () => {
      const { container } = render(<RarityBadge rarity="Legendary" />)
      const badge = container.firstChild as HTMLElement
      expect(badge.className).toContain('bg-accent-gold')
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA label for Common', () => {
      render(<RarityBadge rarity="Common" />)
      const badge = screen.getByLabelText('Rarity: Common')
      expect(badge).toBeInTheDocument()
    })

    it('should have proper ARIA label for all rarities', () => {
      const rarities: Rarity[] = ['Common', 'Rare', 'Epic', 'Legendary']
      rarities.forEach(rarity => {
        const { unmount } = render(<RarityBadge rarity={rarity} />)
        expect(screen.getByLabelText(`Rarity: ${rarity}`)).toBeInTheDocument()
        unmount()
      })
    })
  })

  describe('Custom className', () => {
    it('should accept and apply custom className', () => {
      const { container } = render(<RarityBadge rarity="Common" className="custom-class" />)
      const badge = container.firstChild as HTMLElement
      expect(badge.className).toContain('custom-class')
    })

    it('should merge custom className with default classes', () => {
      const { container } = render(<RarityBadge rarity="Rare" className="extra-padding" />)
      const badge = container.firstChild as HTMLElement
      expect(badge.className).toContain('extra-padding')
      expect(badge.className).toContain('bg-blue')
    })
  })
})
