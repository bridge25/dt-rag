// @CODE:FRONTEND-INTEGRATION-001:DETAIL-CARD
// @CODE:TAILWIND-V4-COMPLETE-001-JIT-FIX-DETAIL-CARD
import { useQuery } from '@tanstack/react-query'
import { calculateCoverage, type CoverageResponse } from '@/lib/api/agents'
import type { AgentCardData } from '@/lib/api/types'
import { RarityBadge } from '@/components/agent-card/RarityBadge'
import { ProgressBar } from '@/components/agent-card/ProgressBar'
import { StatDisplay } from '@/components/agent-card/StatDisplay'
import { cn } from '@/lib/utils'

interface AgentDetailCardProps {
  agent: AgentCardData
}

export function AgentDetailCard({ agent }: AgentDetailCardProps) {
  const { data: coverage, isLoading: isCoverageLoading } = useQuery<CoverageResponse>({
    queryKey: ['coverage', agent.agent_id],
    queryFn: () => calculateCoverage(agent.agent_id),
    staleTime: 30000,
  })

  return (
    <div className={cn(
      'bg-white rounded-lg shadow-lg border-4 p-8',
      agent.rarity === 'Common' && 'border-gray-300',
      agent.rarity === 'Rare' && 'border-blue-400',
      agent.rarity === 'Epic' && 'border-purple-500',
      agent.rarity === 'Legendary' && 'border-accent-gold-500'
    )}>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">{agent.name}</h1>
          <p className="text-xl text-gray-600">Level {agent.level}</p>
        </div>
        <RarityBadge rarity={agent.rarity} className="text-xl px-4 py-2" />
      </div>

      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-700 mb-3">Experience Progress</h2>
        <ProgressBar
          current={agent.current_xp}
          max={agent.next_level_xp || agent.current_xp}
          label={`${agent.current_xp} / ${agent.next_level_xp || 'MAX'} XP`}
          ariaLabel="Experience progress"
          className="h-8"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gray-50 rounded-lg p-4">
          <StatDisplay
            label="Total Documents"
            value={agent.total_documents}
            layout="horizontal"
          />
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <StatDisplay
            label="Total Queries"
            value={agent.total_queries}
            layout="horizontal"
          />
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <StatDisplay
            label="Quality Score"
            value={agent.quality_score}
            layout="horizontal"
            variant="success"
          />
        </div>
      </div>

      {coverage && !isCoverageLoading && (
        <div className="border-t pt-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-700 mb-4">Coverage Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-600">Coverage</span>
                <span className="text-2xl font-bold text-blue-600">
                  {coverage.coverage_percentage.toFixed(1)}%
                </span>
              </div>
              <ProgressBar
                current={coverage.coverage_percentage}
                max={100}
                label=""
                ariaLabel="Coverage percentage"
                className="h-2"
              />
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Documents Covered</span>
                <span className="text-2xl font-bold text-green-600">
                  {coverage.covered_documents} / {coverage.total_documents}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="border-t pt-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">Agent Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-600">Agent ID:</span>
            <span className="ml-2 text-gray-800 font-mono">{agent.agent_id}</span>
          </div>
          <div>
            <span className="font-medium text-gray-600">Status:</span>
            <span className="ml-2 text-gray-800">{agent.status}</span>
          </div>
          <div>
            <span className="font-medium text-gray-600">Created At:</span>
            <span className="ml-2 text-gray-800">
              {new Date(agent.created_at).toLocaleString()}
            </span>
          </div>
          {agent.last_used && (
            <div>
              <span className="font-medium text-gray-600">Last Used:</span>
              <span className="ml-2 text-gray-800">
                {new Date(agent.last_used).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
