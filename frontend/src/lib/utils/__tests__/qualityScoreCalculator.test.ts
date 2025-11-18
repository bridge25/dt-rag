// @TEST:AGENT-CARD-001-UTILS-004
import { describe, it, expect } from 'vitest'
import { calculateQualityScore } from '../qualityScoreCalculator'

describe('qualityScoreCalculator', () => {
  describe('calculateQualityScore', () => {
    it('should return 0 for RAGAS score of 0.0', () => {
      expect(calculateQualityScore(0.0)).toBe(0)
    })

    it('should return 100 for RAGAS score of 1.0', () => {
      expect(calculateQualityScore(1.0)).toBe(100)
    })

    it('should return 50 for RAGAS score of 0.5', () => {
      expect(calculateQualityScore(0.5)).toBe(50)
    })

    it('should return 25 for RAGAS score of 0.25', () => {
      expect(calculateQualityScore(0.25)).toBe(25)
    })

    it('should return 75 for RAGAS score of 0.75', () => {
      expect(calculateQualityScore(0.75)).toBe(75)
    })

    it('should handle decimal RAGAS scores correctly', () => {
      expect(calculateQualityScore(0.123)).toBe(12)
      expect(calculateQualityScore(0.876)).toBe(88)
      expect(calculateQualityScore(0.999)).toBe(100)
    })

    it('should round to nearest integer', () => {
      expect(calculateQualityScore(0.124)).toBe(12)
      expect(calculateQualityScore(0.125)).toBe(13)
      expect(calculateQualityScore(0.875)).toBe(88)
      expect(calculateQualityScore(0.876)).toBe(88)
    })

    describe('Edge cases', () => {
      it('should handle negative values as 0', () => {
        expect(calculateQualityScore(-0.5)).toBe(0)
        expect(calculateQualityScore(-1.0)).toBe(0)
      })

      it('should cap values above 1.0 at 100', () => {
        expect(calculateQualityScore(1.5)).toBe(100)
        expect(calculateQualityScore(2.0)).toBe(100)
      })

      it('should handle very small positive numbers', () => {
        expect(calculateQualityScore(0.001)).toBe(0)
        expect(calculateQualityScore(0.005)).toBe(1)
      })
    })
  })
})
