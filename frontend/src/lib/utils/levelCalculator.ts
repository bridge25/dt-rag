// @CODE:AGENT-CARD-001-UTILS-002

export const LEVEL_THRESHOLDS = [
  0,      // Level 1: 0 XP
  100,    // Level 2: 100 XP
  250,    // Level 3: 250 XP
  500,    // Level 4: 500 XP
  1000,   // Level 5: 1000 XP
  2000,   // Level 6: 2000 XP
  3500,   // Level 7: 3500 XP
  5500,   // Level 8: 5500 XP
  8000,   // Level 9: 8000 XP
  11000   // Level 10: 11000 XP
]

export function calculateLevel(currentXp: number): number {
  for (let i = LEVEL_THRESHOLDS.length - 1; i >= 0; i--) {
    if (currentXp >= LEVEL_THRESHOLDS[i]) {
      return i + 1
    }
  }
  return 1
}

export function getNextLevelXp(currentLevel: number): number | null {
  if (currentLevel >= 10) {
    return null
  }
  return LEVEL_THRESHOLDS[currentLevel]
}
