/**
 * Agent Detail Page
 * Shows detailed information about a specific agent with XP management
 *
 * @CODE:FRONTEND-MIGRATION-002:DETAIL-PAGE
 */
"use client"

import { useState, useRef, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { useAgent } from "@/hooks/useAgent"
import { AgentDetailCard } from "@/components/agent-detail/AgentDetailCard"
import { XPAwardButton } from "@/components/agent-detail/XPAwardButton"
import { LevelUpTimeline } from "@/components/agent-detail/LevelUpTimeline"
import { LevelUpModal } from "@/components/agent-card/LevelUpModal"
import type { Rarity } from "@/lib/api/types"

export default function AgentDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const id = params.id

  const { agent, isLoading, error, refetch } = useAgent(id)
  const [isLevelUpModalOpen, setIsLevelUpModalOpen] = useState(false)
  const [levelUpData, setLevelUpData] = useState<{
    oldLevel: number
    newLevel: number
    rarity: Rarity
  } | null>(null)
  const previousLevel = useRef<number | null>(null)

  // Track level changes for automatic level up modal
  useEffect(() => {
    const currentLevel = agent?.level ?? 1
    if (agent && previousLevel.current !== null && currentLevel > previousLevel.current) {
      setLevelUpData({
        oldLevel: previousLevel.current,
        newLevel: currentLevel,
        rarity: agent.rarity ?? "Common",
      })
      setIsLevelUpModalOpen(true)
    }

    if (agent) {
      previousLevel.current = currentLevel
    }
  }, [agent])

  const handleLevelUp = (oldLevel: number, newLevel: number) => {
    if (agent) {
      setLevelUpData({
        oldLevel,
        newLevel,
        rarity: agent.rarity ?? "Common",
      })
      setIsLevelUpModalOpen(true)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-4xl mx-auto">
          <div className="h-12 bg-white/10 rounded w-48 mb-8 animate-pulse"></div>
          <div className="bg-white/5 rounded-lg border border-white/10 backdrop-blur-md p-8">
            <div className="h-64 bg-white/10 rounded animate-pulse"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-4xl mx-auto">
          <button
            onClick={() => router.back()}
            className="mb-8 text-blue-600 hover:text-blue-800 font-semibold"
          >
            &larr; Back
          </button>
          <div className="bg-white/5 rounded-lg border border-white/10 backdrop-blur-md p-8 text-center">
            <p className="text-red-600 text-lg mb-4">Error: {error.message}</p>
            <p className="text-white/60 mb-6">Failed to load agent details.</p>
            <button
              onClick={() => refetch()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!agent) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-4xl mx-auto">
          <Link
            href="/"
            className="mb-8 text-blue-600 hover:text-blue-800 font-semibold inline-block"
          >
            &larr; Back to Home
          </Link>
          <div className="bg-white/5 rounded-lg border border-white/10 backdrop-blur-md p-8 text-center">
            <p className="text-white/60">Agent not found.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="min-h-screen p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8 flex items-center justify-between">
            <button
              onClick={() => router.back()}
              className="text-blue-400 hover:text-blue-300 font-semibold"
            >
              &larr; Back
            </button>
            <Link
              href={`/agents/${agent.agent_id}/history`}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              View History
            </Link>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-8">
              <AgentDetailCard agent={agent} />
              <LevelUpTimeline agent={agent} />
            </div>

            <div className="lg:col-span-1">
              <div className="bg-white/5 rounded-lg border border-white/10 backdrop-blur-md p-6 sticky top-8">
                <XPAwardButton agentId={agent.agent_id} onLevelUp={handleLevelUp} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {levelUpData && (
        <LevelUpModal
          isOpen={isLevelUpModalOpen}
          onClose={() => setIsLevelUpModalOpen(false)}
          oldLevel={levelUpData.oldLevel}
          newLevel={levelUpData.newLevel}
          rarity={levelUpData.rarity}
        />
      )}
    </>
  )
}
