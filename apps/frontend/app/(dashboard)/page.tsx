/**
 * Home page with Agent Cards - Pokemon-style UI
 * Migrated from Vite frontend per frontend-design-master-plan.md
 *
 * @CODE:FRONTEND-MIGRATION-001
 * @CODE:HOME-STATS-001:HOME-PAGE-REDESIGN
 */

"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAgents } from "@/hooks/useAgents"
import { AgentCard } from "@/components/agent-card"
import { VirtualList } from "@/components/common/VirtualList"
import { LoadingSpinner } from "@/components/common/LoadingSpinner"
import { StatCard } from "@/components/home/StatCard"
import { RecommendationPanel } from "@/components/home/RecommendationPanel"
import { Users, BookOpen, MessageSquare, Folder, Plus } from "lucide-react"

const VIRTUAL_SCROLL_THRESHOLD = 100

export default function HomePage() {
  const router = useRouter()
  const { agents, isLoading, error, refetch } = useAgents()
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })

  useEffect(() => {
    const updateDimensions = () => {
      setDimensions({
        width: window.innerWidth - 64,
        height: window.innerHeight - 200,
      })
    }

    updateDimensions()
    window.addEventListener("resize", updateDimensions)
    return () => window.removeEventListener("resize", updateDimensions)
  }, [])

  const handleView = (agentId: string) => {
    router.push(`/agents/${agentId}`)
  }

  const handleDelete = (agentId: string) => {
    console.log("Delete agent:", agentId)
  }

  const handleCreateAgent = () => {
    router.push("/agents/create")
  }

  // Calculate statistics
  const totalDocuments = agents.reduce((sum, agent) => sum + (agent.total_documents || 0), 0)
  const totalConversations = agents.reduce((sum, agent) => sum + (agent.total_queries || 0), 0)

  if (isLoading) {
    return (
      <main className="p-8">
        <header className="flex items-center gap-6 mb-8">
          <img
            src="/company-logo.jpg"
            alt="Company Logo"
            className="h-16 md:h-20 w-auto object-contain rounded-lg shadow-md"
          />
          <div className="flex-1">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-800 dark:text-gray-100">Agents</h1>
            <p className="text-sm md:text-base text-gray-600 dark:text-gray-400 mt-1">
              Dynamic Taxonomy RAG System
            </p>
          </div>
        </header>
        <LoadingSpinner />
      </main>
    )
  }

  if (error) {
    return (
      <main className="p-8">
        <header className="flex items-center gap-6 mb-8">
          <img
            src="/company-logo.jpg"
            alt="Company Logo"
            className="h-16 md:h-20 w-auto object-contain rounded-lg shadow-md"
          />
          <div className="flex-1">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-800 dark:text-gray-100">Agents</h1>
            <p className="text-sm md:text-base text-gray-600 dark:text-gray-400 mt-1">
              Dynamic Taxonomy RAG System
            </p>
          </div>
        </header>
        <div className="text-center py-12">
          <p className="text-red-600 text-lg mb-4">
            Error: {error.message}
          </p>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Failed to fetch agents. Please try again.
          </p>
          <button
            onClick={() => refetch()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </main>
    )
  }

  // Common layout structure for both empty and populated states
  const renderLayout = (content: React.ReactNode) => (
    <main className="p-8 max-w-7xl mx-auto">
      {/* Header with Logo */}
      <header className="flex items-center gap-6 mb-8">
        <img
          src="/company-logo.jpg"
          alt="Company Logo"
          className="h-16 md:h-20 w-auto object-contain rounded-lg shadow-md"
        />
        <div className="flex-1">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-800 dark:text-gray-100">
            Agents {agents.length > 0 && `(${agents.length})`}
          </h1>
          <p className="text-sm md:text-base text-gray-600 dark:text-gray-400 mt-1">
            Dynamic Taxonomy RAG System
          </p>
        </div>
      </header>

      {/* Statistics Section - Always Visible */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Agents"
          value={agents.length}
          icon={<Users className="w-5 h-5" />}
          description="Total agents"
        />
        <StatCard
          title="Knowledge Base"
          value={totalDocuments}
          icon={<BookOpen className="w-5 h-5" />}
          description="Total documents"
        />
        <StatCard
          title="Conversations"
          value={totalConversations}
          icon={<MessageSquare className="w-5 h-5" />}
          description="Total queries"
        />
        <StatCard
          title="Taxonomy"
          value="v1.0.0"
          icon={<Folder className="w-5 h-5" />}
          description="Current version"
        />
      </div>

      {content}
    </main>
  )

  if (agents.length === 0) {
    return renderLayout(
      <>
        {/* Empty State with Recommendation Panel */}
        <RecommendationPanel hasAgents={false} onCreateAgent={handleCreateAgent} />
      </>
    )
  }

  const useVirtualScroll = agents.length > VIRTUAL_SCROLL_THRESHOLD
  const columnCount = Math.floor(dimensions.width / 320) || 1
  const columnWidth = 320
  const rowHeight = 450

  // Agents exist - show grid with controls
  return renderLayout(
    <>
      {/* Agent Controls */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">My Agents</h2>
          <select className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-gray-100">
            <option>Sort: Recent</option>
            <option>Sort: Level</option>
            <option>Sort: Name</option>
          </select>
          <select className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-gray-100">
            <option>Filter: All Levels</option>
            <option>Filter: Common</option>
            <option>Filter: Rare</option>
            <option>Filter: Epic</option>
            <option>Filter: Legendary</option>
          </select>
        </div>
        <button
          onClick={handleCreateAgent}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          New Agent
        </button>
      </div>

      {/* Agent Grid */}
      {useVirtualScroll ? (
        <div className="flex justify-center mb-8">
          <VirtualList
            agents={agents}
            columnCount={columnCount}
            columnWidth={columnWidth}
            rowHeight={rowHeight}
            height={dimensions.height}
            width={dimensions.width}
            onView={handleView}
            onDelete={handleDelete}
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
          {agents.map((agent) => (
            <AgentCard
              key={agent.agent_id}
              agent={agent}
              onView={() => handleView(agent.agent_id)}
              onDelete={() => handleDelete(agent.agent_id)}
            />
          ))}
        </div>
      )}

      {/* Recommendation Panel */}
      <RecommendationPanel hasAgents={true} />
    </>
  )
}
