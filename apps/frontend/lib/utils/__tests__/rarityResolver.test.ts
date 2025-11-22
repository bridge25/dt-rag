/**
 * Rarity Resolver Tests
 * @TEST:FRONTEND-MIGRATION-001
 */

import { describe, it, expect } from 'vitest'
import { resolveRarity } from '../rarityResolver'

describe('rarityResolver', () => {
  describe('resolveRarity', () => {
    it('returns Common for level 0', () => {
      expect(resolveRarity(0)).toBe('Common')
    })

    it('returns Common for negative level', () => {
      expect(resolveRarity(-5)).toBe('Common')
    })

    it('returns Common for levels 1-3', () => {
      expect(resolveRarity(1)).toBe('Common')
      expect(resolveRarity(2)).toBe('Common')
      expect(resolveRarity(3)).toBe('Common')
    })

    it('returns Rare for levels 4-6', () => {
      expect(resolveRarity(4)).toBe('Rare')
      expect(resolveRarity(5)).toBe('Rare')
      expect(resolveRarity(6)).toBe('Rare')
    })

    it('returns Epic for levels 7-8', () => {
      expect(resolveRarity(7)).toBe('Epic')
      expect(resolveRarity(8)).toBe('Epic')
    })

    it('returns Legendary for level 9+', () => {
      expect(resolveRarity(9)).toBe('Legendary')
      expect(resolveRarity(10)).toBe('Legendary')
      expect(resolveRarity(100)).toBe('Legendary')
    })
  })
})
