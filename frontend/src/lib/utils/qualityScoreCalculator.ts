// @CODE:AGENT-CARD-001-UTILS-004

export function calculateQualityScore(ragasScore: number): number {
  const clamped = Math.max(0, Math.min(1, ragasScore))
  const percentage = clamped * 100
  return Math.round(percentage)
}
