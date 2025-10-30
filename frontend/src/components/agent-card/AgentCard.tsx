// @CODE:AGENT-CARD-001-UI-005
import { memo } from 'react'
import { cn } from '@/lib/utils'
import type { AgentCardData } from '@/lib/api/types'
import { RarityBadge } from './RarityBadge'
import { ProgressBar } from './ProgressBar'
import { StatDisplay } from './StatDisplay'
import { ActionButtons } from './ActionButtons'

interface AgentCardProps {
  agent: AgentCardData
  onView: () => void
  onDelete: () => void
  className?: string
}

const rarityBorderStyles = {
  Common: 'border-gray-300',
  Rare: 'border-blue-400',
  Epic: 'border-purple-500',
  Legendary: 'border-accent-gold',
}

export const AgentCard = memo<AgentCardProps>(function AgentCard({ agent, onView, onDelete, className }) {
  return (
    <article
      role="article"
      aria-label={`${agent.name} - Level ${agent.level} ${agent.rarity} agent`}
      className={cn(
        'w-[280px] p-4 bg-white rounded-lg border-2 shadow-md hover:shadow-lg transition-shadow',
        rarityBorderStyles[agent.rarity],
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-bold text-gray-900">{agent.name}</h3>
          <p className="text-sm text-gray-600">Level {agent.level}</p>
        </div>
        <RarityBadge rarity={agent.rarity} />
      </div>

      {/* XP Progress */}
      <div className="mb-4">
        <ProgressBar
          current={agent.current_xp}
          max={agent.next_level_xp || agent.current_xp}
          label={`${agent.current_xp} / ${agent.next_level_xp || 'MAX'} XP`}
          ariaLabel="Experience progress"
        />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <StatDisplay label="Docs" value={agent.total_documents} layout="vertical" />
        <StatDisplay label="Queries" value={agent.total_queries} layout="vertical" />
        <StatDisplay label="Quality" value={agent.quality_score} layout="vertical" variant="success" />
      </div>

      {/* Action Buttons */}
      <ActionButtons onView={onView} onDelete={onDelete} agentName={agent.name} />
    </article>
  )
})
