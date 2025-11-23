/**
 * Agent History Page
 * Shows historical data and analytics for a specific agent
 *
 * @CODE:FRONTEND-MIGRATION-002:HISTORY-PAGE
 */
"use client"

import { useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { useAgent } from "@/hooks/useAgent"
import { useCoverageHistory } from "@/hooks/useCoverageHistory"
import { ChartContainer } from "@/components/history/ChartContainer"
import { CoverageChart } from "@/components/history/CoverageChart"
import { XPGrowthChart } from "@/components/history/XPGrowthChart"

export default function AgentHistoryPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const id = params.id

  const { agent, isLoading, error } = useAgent(id)
  const [period, setPeriod] = useState(30)
  const { data: historyData, isLoading: isHistoryLoading } = useCoverageHistory(
    id,
    {
      interval: "daily",
    }
  )

  const handlePeriodChange = (days: number) => {
    setPeriod(days)
  }

  const filteredHistory = historyData?.history.slice(-period) || []

  if (isLoading) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-6xl mx-auto">
          <div className="h-12 bg-gray-200 rounded w-48 mb-8 animate-pulse"></div>
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="h-96 bg-gray-200 rounded animate-pulse"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-6xl mx-auto">
          <button
            onClick={() => router.back()}
            className="mb-8 text-blue-600 hover:text-blue-800 font-semibold"
          >
            &larr; Back
          </button>
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <p className="text-red-600 text-lg mb-4">Error: {error.message}</p>
            <p className="text-gray-600">Failed to load agent history.</p>
          </div>
        </div>
      </div>
    )
  }

  if (!agent) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-6xl mx-auto">
          <Link
            href="/"
            className="mb-8 text-blue-600 hover:text-blue-800 font-semibold inline-block"
          >
            &larr; Back to Home
          </Link>
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <p className="text-gray-600">Agent not found.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-6xl mx-auto">
        {/* Navigation */}
        <div className="mb-8 flex items-center justify-between">
          <button
            onClick={() => router.back()}
            className="text-blue-600 hover:text-blue-800 font-semibold"
          >
            &larr; Back
          </button>
          <Link
            href={`/agents/${agent.agent_id}`}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            View Details
          </Link>
        </div>

        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {agent.name} - History & Analytics
          </h1>
          <p className="text-gray-600">
            Level {agent.level} &bull; {agent.rarity} &bull; {agent.current_xp} XP
          </p>
        </div>

        {/* Charts */}
        <ChartContainer onPeriodChange={handlePeriodChange}>
          {isHistoryLoading ? (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="h-96 bg-gray-200 rounded animate-pulse"></div>
            </div>
          ) : filteredHistory.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <CoverageChart data={filteredHistory} />
              <XPGrowthChart data={filteredHistory} />
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-lg p-6 text-center">
              <p className="text-gray-500">No history data available</p>
            </div>
          )}
        </ChartContainer>

        {/* Stats Summary */}
        <div className="bg-white rounded-lg shadow-lg p-6 mt-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Summary Statistics
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded p-4">
              <p className="text-sm text-gray-600 mb-1">Total Documents</p>
              <p className="text-2xl font-bold text-gray-900">
                {agent.total_documents}
              </p>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <p className="text-sm text-gray-600 mb-1">Total Queries</p>
              <p className="text-2xl font-bold text-gray-900">
                {agent.total_queries}
              </p>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <p className="text-sm text-gray-600 mb-1">Quality Score</p>
              <p className="text-2xl font-bold text-green-600">
                {agent.quality_score}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
