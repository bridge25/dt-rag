/**
 * Quality Score Calculator Tests
 * @TEST:FRONTEND-MIGRATION-001
 */

import { describe, it, expect } from 'vitest'
import { calculateQualityScore } from '../qualityScoreCalculator'

describe('qualityScoreCalculator', () => {
  describe('calculateQualityScore', () => {
    it('returns 0 for score 0', () => {
      expect(calculateQualityScore(0)).toBe(0)
    })

    it('returns 100 for score 1', () => {
      expect(calculateQualityScore(1)).toBe(100)
    })

    it('returns 50 for score 0.5', () => {
      expect(calculateQualityScore(0.5)).toBe(50)
    })

    it('clamps negative values to 0', () => {
      expect(calculateQualityScore(-0.5)).toBe(0)
    })

    it('clamps values above 1 to 100', () => {
      expect(calculateQualityScore(1.5)).toBe(100)
    })

    it('rounds to nearest integer', () => {
      expect(calculateQualityScore(0.333)).toBe(33)
      expect(calculateQualityScore(0.666)).toBe(67)
    })
  })
})
