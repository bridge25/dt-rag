/**
 * Level Calculator Tests
 * @TEST:FRONTEND-MIGRATION-001
 */

import { describe, it, expect } from 'vitest'
import { calculateLevel, getNextLevelXp, LEVEL_THRESHOLDS } from '../levelCalculator'

describe('levelCalculator', () => {
  describe('calculateLevel', () => {
    it('returns level 1 for 0 XP', () => {
      expect(calculateLevel(0)).toBe(1)
    })

    it('returns level 1 for negative XP', () => {
      expect(calculateLevel(-100)).toBe(1)
    })

    it('returns level 2 for 100 XP', () => {
      expect(calculateLevel(100)).toBe(2)
    })

    it('returns level 2 for 249 XP', () => {
      expect(calculateLevel(249)).toBe(2)
    })

    it('returns level 10 for max XP', () => {
      expect(calculateLevel(11000)).toBe(10)
    })

    it('returns level 10 for XP beyond max', () => {
      expect(calculateLevel(99999)).toBe(10)
    })
  })

  describe('getNextLevelXp', () => {
    it('returns 100 for level 1', () => {
      expect(getNextLevelXp(1)).toBe(100)
    })

    it('returns null for level 10', () => {
      expect(getNextLevelXp(10)).toBeNull()
    })

    it('returns correct thresholds', () => {
      expect(getNextLevelXp(5)).toBe(LEVEL_THRESHOLDS[5])
    })
  })
})
