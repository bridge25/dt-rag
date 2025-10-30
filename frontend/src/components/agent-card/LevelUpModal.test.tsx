// @TEST:AGENT-CARD-001-ANIM-001
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import type { Rarity } from '@/lib/api/types'

vi.mock('react-confetti', () => ({
  default: vi.fn(() => null),
}))

import { LevelUpModal } from './LevelUpModal'

describe('LevelUpModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Basic Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(
        <LevelUpModal
          isOpen={false}
          onClose={vi.fn()}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      expect(screen.queryByText('Level Up!')).not.toBeInTheDocument()
    })

    it('should render when isOpen is true', () => {
      render(
        <LevelUpModal
          isOpen={true}
          onClose={vi.fn()}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      expect(screen.getByText('Level Up!')).toBeInTheDocument()
    })

    it('should display level progression correctly', () => {
      render(
        <LevelUpModal
          isOpen={true}
          onClose={vi.fn()}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      expect(screen.getByText(/Lv\.3/)).toBeInTheDocument()
      expect(screen.getByText(/Lv\.4/)).toBeInTheDocument()
      expect(screen.getByText(/→/)).toBeInTheDocument()
    })

    it('should display rarity information', () => {
      render(
        <LevelUpModal
          isOpen={true}
          onClose={vi.fn()}
          oldLevel={5}
          newLevel={6}
          rarity="Epic"
        />
      )

      expect(screen.getByText(/Epic/)).toBeInTheDocument()
    })
  })

  describe('Rarity Upgrade Display', () => {
    it('should show rarity upgrade when upgradeRarity is provided', () => {
      render(
        <LevelUpModal
          isOpen={true}
          onClose={vi.fn()}
          oldLevel={5}
          newLevel={6}
          rarity="Rare"
          upgradeRarity="Epic"
        />
      )

      expect(screen.getByText(/Rare/)).toBeInTheDocument()
      expect(screen.getByText(/Epic/)).toBeInTheDocument()
      expect(screen.getByText(/Rarity Upgrade/i)).toBeInTheDocument()
    })

    it('should not show rarity upgrade when upgradeRarity is not provided', () => {
      render(
        <LevelUpModal
          isOpen={true}
          onClose={vi.fn()}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      expect(screen.queryByText(/Rarity Upgrade/i)).not.toBeInTheDocument()
    })
  })

  describe('Auto-close Behavior', () => {
    it('should auto-close after 3 seconds', async () => {
      const onClose = vi.fn()

      render(
        <LevelUpModal
          isOpen={true}
          onClose={onClose}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      expect(onClose).not.toHaveBeenCalled()

      await act(async () => {
        vi.advanceTimersByTime(3000)
      })

      expect(onClose).toHaveBeenCalledTimes(1)
    })

    it('should not auto-close if modal is closed before timeout', () => {
      const onClose = vi.fn()

      const { rerender } = render(
        <LevelUpModal
          isOpen={true}
          onClose={onClose}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      rerender(
        <LevelUpModal
          isOpen={false}
          onClose={onClose}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      vi.advanceTimersByTime(3000)

      expect(onClose).toHaveBeenCalledTimes(0)
    })

    it('should clear timeout on unmount', () => {
      const onClose = vi.fn()

      const { unmount } = render(
        <LevelUpModal
          isOpen={true}
          onClose={onClose}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      unmount()
      vi.advanceTimersByTime(3000)

      expect(onClose).not.toHaveBeenCalled()
    })
  })

  describe('Confetti Integration', () => {
    it('should render confetti when modal is open', async () => {
      const Confetti = await import('react-confetti')

      render(
        <LevelUpModal
          isOpen={true}
          onClose={vi.fn()}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      expect(Confetti.default).toHaveBeenCalled()
    })

    it('should not render confetti when modal is closed', async () => {
      const Confetti = await import('react-confetti')
      vi.mocked(Confetti.default).mockClear()

      render(
        <LevelUpModal
          isOpen={false}
          onClose={vi.fn()}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      expect(Confetti.default).not.toHaveBeenCalled()
    })

    it('should pass recycle=false to confetti for one-time effect', async () => {
      const Confetti = await import('react-confetti')
      vi.mocked(Confetti.default).mockClear()

      render(
        <LevelUpModal
          isOpen={true}
          onClose={vi.fn()}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      expect(Confetti.default).toHaveBeenCalledWith(
        expect.objectContaining({
          recycle: false,
          numberOfPieces: 200,
          gravity: 0.3
        }),
        undefined
      )
    })
  })

  describe('Animation Variants', () => {
    it('should apply animation classes to modal container', () => {
      const { container } = render(
        <LevelUpModal
          isOpen={true}
          onClose={vi.fn()}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      const backdrop = container.querySelector('[data-testid="modal-backdrop"]')
      expect(backdrop).toBeInTheDocument()
    })

    it('should have proper backdrop styling', () => {
      const { container } = render(
        <LevelUpModal
          isOpen={true}
          onClose={vi.fn()}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      const backdrop = container.querySelector('[data-testid="modal-backdrop"]')
      expect(backdrop).toHaveClass('fixed', 'inset-0', 'bg-black/50')
    })
  })

  describe('Edge Cases', () => {
    it('should handle single level increase', () => {
      render(
        <LevelUpModal
          isOpen={true}
          onClose={vi.fn()}
          oldLevel={1}
          newLevel={2}
          rarity="Common"
        />
      )

      expect(screen.getByText(/Lv\.1/)).toBeInTheDocument()
      expect(screen.getByText(/Lv\.2/)).toBeInTheDocument()
    })

    it('should handle multiple level increase', () => {
      render(
        <LevelUpModal
          isOpen={true}
          onClose={vi.fn()}
          oldLevel={5}
          newLevel={8}
          rarity="Epic"
        />
      )

      expect(screen.getByText(/Lv\.5/)).toBeInTheDocument()
      expect(screen.getByText(/Lv\.8/)).toBeInTheDocument()
    })

    it('should handle max level (10)', () => {
      render(
        <LevelUpModal
          isOpen={true}
          onClose={vi.fn()}
          oldLevel={9}
          newLevel={10}
          rarity="Legendary"
        />
      )

      expect(screen.getByText(/Lv\.10/)).toBeInTheDocument()
    })

    it('should handle all rarity types', () => {
      const rarities: Rarity[] = ['Common', 'Rare', 'Epic', 'Legendary']

      rarities.forEach(rarity => {
        const { unmount } = render(
          <LevelUpModal
            isOpen={true}
            onClose={vi.fn()}
            oldLevel={3}
            newLevel={4}
            rarity={rarity}
          />
        )

        expect(screen.getByText(rarity)).toBeInTheDocument()
        unmount()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(
        <LevelUpModal
          isOpen={true}
          onClose={vi.fn()}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-labelledby', 'level-up-title')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
    })

    it('should have descriptive title', () => {
      render(
        <LevelUpModal
          isOpen={true}
          onClose={vi.fn()}
          oldLevel={3}
          newLevel={4}
          rarity="Rare"
        />
      )

      const title = screen.getByRole('heading', { name: /Level Up!/i })
      expect(title).toHaveAttribute('id', 'level-up-title')
    })
  })
})
