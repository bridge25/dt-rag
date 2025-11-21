/**
 * Rarity level resolution based on agent level
 *
 * @CODE:FRONTEND-001
 */

export type Rarity = 'Common' | 'Rare' | 'Epic' | 'Legendary'

export function resolveRarity(level: number): Rarity {
  if (level <= 0) {
    return 'Common'
  }

  if (level >= 9) {
    return 'Legendary'
  }

  if (level >= 7) {
    return 'Epic'
  }

  if (level >= 4) {
    return 'Rare'
  }

  return 'Common'
}
