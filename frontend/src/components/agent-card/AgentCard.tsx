// @CODE:AGENT-CARD-001-UI-005
// @CODE:POKEMON-IMAGE-COMPLETE-001-CARD-001
import { memo } from 'react'
import { cn } from '@/lib/utils'
import type { AgentCardData } from '@/lib/api/types'
import { RarityBadge } from './RarityBadge'
import { ProgressBar } from './ProgressBar'
import { StatDisplay } from './StatDisplay'
import { ActionButtons } from './ActionButtons'
import { AgentCardAvatar } from './AgentCardAvatar'

interface AgentCardProps {
  agent: AgentCardData
  onView: () => void
  onDelete: () => void
  className?: string
}

// @CODE:FRONTEND-INTEGRATION-001-MEMO-CARDS
const arePropsEqual = (prevProps: AgentCardProps, nextProps: AgentCardProps) => {
  return (
    prevProps.agent.agent_id === nextProps.agent.agent_id &&
    prevProps.agent.current_xp === nextProps.agent.current_xp &&
    prevProps.agent.level === nextProps.agent.level &&
    prevProps.agent.rarity === nextProps.agent.rarity &&
    prevProps.className === nextProps.className
  )
}

export const AgentCard = memo<AgentCardProps>(function AgentCard({ agent, onView, onDelete, className }) {
  return (
    <article
      role="article"
      aria-label={`${agent.name} - Level ${agent.level} ${agent.rarity} agent`}
      className={cn(
        'w-full p-4 bg-white rounded-lg border-2 shadow-md hover:shadow-lg transition-shadow',
        // Tailwind v4 JIT requires explicit class names
        agent.rarity.toLowerCase() === 'common' && 'border-gray-300',
        agent.rarity.toLowerCase() === 'rare' && 'border-blue-400',
        agent.rarity.toLowerCase() === 'epic' && 'border-purple-500',
        agent.rarity.toLowerCase() === 'legendary' && 'border-accent-gold-500',
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

      {/* CHARACTER IMAGE SECTION (Pokemon Style) */}
      <div className="mb-4">
        <AgentCardAvatar
          agentId={agent.agent_id}
          agentName={agent.name}
          rarity={agent.rarity}
          avatarUrl={agent.avatar_url}
        />
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
}, arePropsEqual)
