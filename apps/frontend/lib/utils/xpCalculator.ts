/**
 * XP calculation utilities
 *
 * @CODE:FRONTEND-MIGRATION-001
 */

export type XpAction = "CHAT" | "FEEDBACK" | "RAGAS"

const XP_VALUES: Record<XpAction, number> = {
  CHAT: 10,
  FEEDBACK: 50,
  RAGAS: 100
}

export function calculateXp(action: XpAction | XpAction[]): number {
  if (Array.isArray(action)) {
    return action.reduce((total, act) => total + XP_VALUES[act], 0)
  }
  return XP_VALUES[action]
}
