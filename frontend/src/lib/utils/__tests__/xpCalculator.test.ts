// @TEST:AGENT-CARD-001-UTILS-001
import { describe, it, expect } from 'vitest'
import { calculateXp, XpAction } from '../xpCalculator'

describe('xpCalculator', () => {
  describe('calculateXp', () => {
    it('should return 10 XP for CHAT action', () => {
      const result = calculateXp('CHAT')
      expect(result).toBe(10)
    })

    it('should return 50 XP for FEEDBACK action', () => {
      const result = calculateXp('FEEDBACK')
      expect(result).toBe(50)
    })

    it('should return 100 XP for RAGAS action', () => {
      const result = calculateXp('RAGAS')
      expect(result).toBe(100)
    })

    it('should handle array of actions', () => {
      const actions: XpAction[] = ['CHAT', 'CHAT', 'FEEDBACK']
      const result = calculateXp(actions)
      expect(result).toBe(70) // 10 + 10 + 50
    })

    it('should return 0 for empty array', () => {
      const result = calculateXp([])
      expect(result).toBe(0)
    })

    it('should calculate total XP for multiple RAGAS actions', () => {
      const actions: XpAction[] = ['RAGAS', 'RAGAS', 'CHAT']
      const result = calculateXp(actions)
      expect(result).toBe(210) // 100 + 100 + 10
    })

    it('should calculate mixed actions correctly', () => {
      const actions: XpAction[] = ['CHAT', 'FEEDBACK', 'RAGAS']
      const result = calculateXp(actions)
      expect(result).toBe(160) // 10 + 50 + 100
    })
  })
})
