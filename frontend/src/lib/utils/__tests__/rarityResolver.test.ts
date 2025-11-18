// @TEST:AGENT-CARD-001-UTILS-003
import { describe, it, expect } from 'vitest'
import { resolveRarity, Rarity } from '../rarityResolver'

describe('rarityResolver', () => {
  describe('resolveRarity', () => {
    describe('Common rarity (Level 1-3)', () => {
      it('should return Common for level 1', () => {
        expect(resolveRarity(1)).toBe('Common')
      })

      it('should return Common for level 2', () => {
        expect(resolveRarity(2)).toBe('Common')
      })

      it('should return Common for level 3', () => {
        expect(resolveRarity(3)).toBe('Common')
      })
    })

    describe('Rare rarity (Level 4-6)', () => {
      it('should return Rare for level 4', () => {
        expect(resolveRarity(4)).toBe('Rare')
      })

      it('should return Rare for level 5', () => {
        expect(resolveRarity(5)).toBe('Rare')
      })

      it('should return Rare for level 6', () => {
        expect(resolveRarity(6)).toBe('Rare')
      })
    })

    describe('Epic rarity (Level 7-8)', () => {
      it('should return Epic for level 7', () => {
        expect(resolveRarity(7)).toBe('Epic')
      })

      it('should return Epic for level 8', () => {
        expect(resolveRarity(8)).toBe('Epic')
      })
    })

    describe('Legendary rarity (Level 9-10)', () => {
      it('should return Legendary for level 9', () => {
        expect(resolveRarity(9)).toBe('Legendary')
      })

      it('should return Legendary for level 10', () => {
        expect(resolveRarity(10)).toBe('Legendary')
      })
    })

    describe('Edge cases', () => {
      it('should return Common for level 0 or below', () => {
        expect(resolveRarity(0)).toBe('Common')
        expect(resolveRarity(-1)).toBe('Common')
      })

      it('should return Legendary for level above 10', () => {
        expect(resolveRarity(11)).toBe('Legendary')
        expect(resolveRarity(100)).toBe('Legendary')
      })
    })

    describe('Type safety', () => {
      it('should return valid Rarity type', () => {
        const validRarities: Rarity[] = ['Common', 'Rare', 'Epic', 'Legendary']
        const result = resolveRarity(5)
        expect(validRarities).toContain(result)
      })
    })
  })
})
