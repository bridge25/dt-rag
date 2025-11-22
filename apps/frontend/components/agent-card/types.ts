/**
 * Agent Card Type Definitions
 * Re-exports from lib/api/types for consistency
 * @CODE:FRONTEND-MIGRATION-001
 */

import type { Rarity as RarityType } from "@/lib/api/types"

// Re-export from centralized types
export type { Rarity, AgentCardData } from "@/lib/api/types"

// Use imported type for function parameter
type Rarity = RarityType

// Lucide icon names for each rarity tier
const COMMON_ICONS = ["Bot", "Cpu", "Database", "Server"]
const RARE_ICONS = ["Brain", "Sparkles", "Zap", "Star"]
const EPIC_ICONS = ["Flame", "Shield", "Crown", "Gem"]
const LEGENDARY_ICONS = ["Rocket", "Trophy", "Award", "Medal"]

// Hash function for deterministic icon selection
function hashString(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = (hash << 5) - hash + char
    hash = hash & hash
  }
  return Math.abs(hash)
}

export function getDefaultAvatarIcon(rarity: Rarity, agentId: string): string {
  const hash = hashString(agentId)
  const icons =
    rarity === "Common"
      ? COMMON_ICONS
      : rarity === "Rare"
        ? RARE_ICONS
        : rarity === "Epic"
          ? EPIC_ICONS
          : LEGENDARY_ICONS
  return icons[hash % icons.length]
}
