/**
 * XP Calculator Tests
 * @TEST:FRONTEND-MIGRATION-001
 */

import { describe, it, expect } from 'vitest'
import { calculateXp, type XpAction } from '../xpCalculator'

describe('xpCalculator', () => {
  describe('calculateXp', () => {
    it('returns 10 for CHAT action', () => {
      expect(calculateXp('CHAT')).toBe(10)
    })

    it('returns 50 for FEEDBACK action', () => {
      expect(calculateXp('FEEDBACK')).toBe(50)
    })

    it('returns 100 for RAGAS action', () => {
      expect(calculateXp('RAGAS')).toBe(100)
    })

    it('calculates sum for array of actions', () => {
      const actions: XpAction[] = ['CHAT', 'FEEDBACK', 'RAGAS']
      expect(calculateXp(actions)).toBe(160)
    })

    it('returns 0 for empty array', () => {
      expect(calculateXp([])).toBe(0)
    })

    it('handles duplicate actions', () => {
      const actions: XpAction[] = ['CHAT', 'CHAT', 'CHAT']
      expect(calculateXp(actions)).toBe(30)
    })
  })
})
