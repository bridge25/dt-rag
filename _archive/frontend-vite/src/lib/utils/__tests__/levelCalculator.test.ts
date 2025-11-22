/**
 * Test file
 *
 * @CODE:FRONTEND-001
 * @TEST:FRONTEND-001
 */
import { describe, it, expect } from 'vitest'
import { calculateLevel, getNextLevelXp, LEVEL_THRESHOLDS } from '../levelCalculator'

describe('levelCalculator', () => {
  describe('calculateLevel', () => {
    it('should return level 1 for 0 XP', () => {
      expect(calculateLevel(0)).toBe(1)
    })

    it('should return level 1 for XP below level 2 threshold', () => {
      expect(calculateLevel(50)).toBe(1)
      expect(calculateLevel(99)).toBe(1)
    })

    it('should return level 2 for 100 XP', () => {
      expect(calculateLevel(100)).toBe(2)
    })

    it('should return level 3 for 250 XP', () => {
      expect(calculateLevel(250)).toBe(3)
    })

    it('should return level 5 for 1000 XP', () => {
      expect(calculateLevel(1000)).toBe(5)
    })

    it('should return level 10 for very high XP', () => {
      expect(calculateLevel(11000)).toBe(10)
      expect(calculateLevel(100000)).toBe(10)
    })

    it('should have consistent level progression', () => {
      // Test boundaries for each level
      expect(calculateLevel(0)).toBe(1)
      expect(calculateLevel(100)).toBe(2)
      expect(calculateLevel(250)).toBe(3)
      expect(calculateLevel(500)).toBe(4)
      expect(calculateLevel(1000)).toBe(5)
      expect(calculateLevel(2000)).toBe(6)
      expect(calculateLevel(3500)).toBe(7)
      expect(calculateLevel(5500)).toBe(8)
      expect(calculateLevel(8000)).toBe(9)
      expect(calculateLevel(11000)).toBe(10)
    })
  })

  describe('getNextLevelXp', () => {
    it('should return 100 XP for level 1', () => {
      expect(getNextLevelXp(1)).toBe(100)
    })

    it('should return 250 XP for level 2', () => {
      expect(getNextLevelXp(2)).toBe(250)
    })

    it('should return 500 XP for level 3', () => {
      expect(getNextLevelXp(3)).toBe(500)
    })

    it('should return null for level 10 (max level)', () => {
      expect(getNextLevelXp(10)).toBe(null)
    })

    it('should return null for levels above 10', () => {
      expect(getNextLevelXp(11)).toBe(null)
      expect(getNextLevelXp(100)).toBe(null)
    })
  })

  describe('LEVEL_THRESHOLDS', () => {
    it('should have 10 levels defined', () => {
      expect(LEVEL_THRESHOLDS.length).toBe(10)
    })

    it('should have increasing XP requirements', () => {
      for (let i = 1; i < LEVEL_THRESHOLDS.length; i++) {
        expect(LEVEL_THRESHOLDS[i]).toBeGreaterThan(LEVEL_THRESHOLDS[i - 1])
      }
    })
  })
})
