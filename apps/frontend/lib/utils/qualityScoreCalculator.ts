/**
 * Quality score calculation from RAGAS scores
 *
 * @CODE:FRONTEND-MIGRATION-001
 */

export function calculateQualityScore(ragasScore: number): number {
  const clamped = Math.max(0, Math.min(1, ragasScore))
  const percentage = clamped * 100
  return Math.round(percentage)
}
