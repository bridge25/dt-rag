/**
 * Agent Card Type Definitions
 * @CODE:FRONTEND-MIGRATION-001
 */

export type Rarity = "Common" | "Rare" | "Epic" | "Legendary"

export interface AgentCardData {
  agent_id: string
  name: string
  level: number
  current_xp: number
  next_level_xp: number | null
  rarity: Rarity
  total_documents: number
  total_queries: number
  quality_score: number
  avatar_url?: string | null
}

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
