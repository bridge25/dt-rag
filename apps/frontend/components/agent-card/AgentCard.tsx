"use client"

/**
 * AgentCard Component - Enhanced Ethereal Glass Design
 * Uses GlassCard base component and RobotAvatar for enhanced visual hierarchy
 * @CODE:FRONTEND-MIGRATION-003
 */

import { memo } from "react"
import { cn } from "@/lib/utils"
import { GlassCard } from "@/components/ui/glass-card"
import { RobotAvatar } from "@/components/ui/robot-avatar"
import type { AgentCardData } from "./types"
import type { Rarity } from "@/lib/ethereal-glass"
import { RarityBadge } from "./RarityBadge"
import { ProgressBar } from "./ProgressBar"
import { StatDisplay } from "./StatDisplay"
import { ActionButtons } from "./ActionButtons"

interface AgentCardProps {
  agent: AgentCardData
  onView: () => void
  onDelete: () => void
  className?: string
}

const arePropsEqual = (
  prevProps: AgentCardProps,
  nextProps: AgentCardProps
) => {
  return (
    prevProps.agent.agent_id === nextProps.agent.agent_id &&
    prevProps.agent.current_xp === nextProps.agent.current_xp &&
    prevProps.agent.level === nextProps.agent.level &&
    prevProps.agent.rarity === nextProps.agent.rarity &&
    prevProps.className === nextProps.className
  )
}

// Convert AgentCardData rarity to lowercase for ethereal-glass
function normalizeRarity(rarity: string): Rarity {
  const rarityMap: Record<string, Rarity> = {
    Common: "common",
    Rare: "rare",
    Epic: "epic",
    Legendary: "legendary",
  }
  return rarityMap[rarity] || "common"
}

// Determine robot name from agent - use agent name as fallback
function getRobotName(agent: AgentCardData): string {
  // If agent has a specific robot type, use it; otherwise convert agent name to lowercase
  if (agent.robot) {
    return agent.robot.toLowerCase()
  }
  // Fallback: convert agent name to a valid robot name
  const validRobots = [
    "analyst", "builder", "explorer", "guardian", "innovator",
    "mentor", "optimizer", "pioneer", "researcher", "strategist",
    "synthesizer", "tracker", "validator", "visionary", "warden", "wizard"
  ]
  const agentNameLower = agent.name.toLowerCase()
  return validRobots.includes(agentNameLower) ? agentNameLower : "analyst"
}

export const AgentCard = memo<AgentCardProps>(function AgentCard({
  agent,
  onView,
  onDelete,
  className,
}) {
  const rarityNormalized = normalizeRarity(agent.rarity)
  const robotName = getRobotName(agent)

  return (
    <GlassCard
      rarity={rarityNormalized}
      className={cn(
        "group relative w-full h-full p-5 rounded-3xl",
        "flex flex-col gap-4",
        className
      )}
    >
      <article
        role="article"
        aria-label={`${agent.name} - Level ${agent.level} ${agent.rarity} agent`}
        className="w-full h-full flex flex-col gap-4"
      >
        {/* Header with Rarity Badge */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-white tracking-tight group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-gray-400 transition-all duration-300 line-clamp-2">
              {agent.name}
            </h3>
            <p className="text-xs text-gray-400 font-medium mt-0.5">
              Level {agent.level}
            </p>
          </div>
          <RarityBadge rarity={agent.rarity} />
        </div>

        {/* Robot Avatar - Centered */}
        <div className="flex justify-center py-2">
          <RobotAvatar
            robot={robotName}
            rarity={rarityNormalized}
            size="md"
          />
        </div>

        {/* XP Progress Bar */}
        <div className="w-full">
          <ProgressBar
            current={agent.current_xp}
            max={agent.next_level_xp || agent.current_xp}
            label={`${agent.current_xp} / ${agent.next_level_xp || "MAX"} XP`}
            ariaLabel="Experience progress"
          />
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-2 p-3 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm">
          <StatDisplay
            label="Docs"
            value={agent.total_documents}
            layout="vertical"
          />
          <StatDisplay
            label="Queries"
            value={agent.total_queries}
            layout="vertical"
          />
          <StatDisplay
            label="Quality"
            value={agent.quality_score}
            layout="vertical"
            variant="success"
          />
        </div>

        {/* Action Buttons - Bottom */}
        <div className="pt-2 border-t border-white/5 mt-auto">
          <ActionButtons
            onView={onView}
            onDelete={onDelete}
            agentName={agent.name}
          />
        </div>
      </article>
    </GlassCard>
  )
}, arePropsEqual)
