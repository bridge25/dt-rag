"use client"

/**
 * AgentCard Component - Ethereal Glass Design
 * @CODE:FRONTEND-MIGRATION-002
 */

import { memo } from "react"
import { cn } from "@/lib/utils"
import type { AgentCardData } from "./types"
import { RarityBadge } from "./RarityBadge"
import { ProgressBar } from "./ProgressBar"
import { StatDisplay } from "./StatDisplay"
import { ActionButtons } from "./ActionButtons"
import { AgentCardAvatar } from "./AgentCardAvatar"

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

export const AgentCard = memo<AgentCardProps>(function AgentCard({
  agent,
  onView,
  onDelete,
  className,
}) {
  // Determine border color based on rarity
  const rarityBorderColor = {
    Common: "border-gray-400",
    Rare: "border-blue-400",
    Epic: "border-purple-500",
    Legendary: "border-amber-500",
  }[agent.rarity] || "border-white/5"

  return (
    <article
      role="article"
      aria-label={`${agent.name} - Level ${agent.level} ${agent.rarity} agent`}
      className={cn(
        "group relative w-full p-5 rounded-3xl transition-all duration-300",
        "bg-glass backdrop-blur-md border",
        rarityBorderColor,
        "hover:shadow-glass-hover hover:-translate-y-1",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-white tracking-tight group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-gray-400 transition-all">
            {agent.name}
          </h3>
          <p className="text-sm text-gray-400 font-medium">Level {agent.level}</p>
        </div>
        <RarityBadge rarity={agent.rarity} />
      </div>

      {/* Avatar */}
      <div className="mb-5">
        <AgentCardAvatar
          agentId={agent.agent_id}
          agentName={agent.name}
          rarity={agent.rarity}
          avatarUrl={agent.avatar_url}
        />
      </div>

      {/* XP Progress */}
      <div className="mb-5">
        <ProgressBar
          current={agent.current_xp}
          max={agent.next_level_xp || agent.current_xp}
          label={`${agent.current_xp} / ${agent.next_level_xp || "MAX"} XP`}
          ariaLabel="Experience progress"
        />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-2 mb-5 p-3 rounded-2xl bg-white/5 border border-white/5">
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

      {/* Action Buttons */}
      <div className="pt-2 border-t border-white/5">
        <ActionButtons onView={onView} onDelete={onDelete} agentName={agent.name} />
      </div>
    </article>
  )
}, arePropsEqual)
