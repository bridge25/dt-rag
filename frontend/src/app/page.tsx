// @CODE:AGENT-CARD-001-PAGE-001
// @CODE:FRONTEND-INTEGRATION-001-HOME-PAGE-UPDATE
'use client'

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAgents } from '../hooks/useAgents'
import { AgentCard } from '../components/agent-card/AgentCard'
import { VirtualList } from '../components/common/VirtualList'
import { LoadingSpinner } from '../components/common/LoadingSpinner'

const VIRTUAL_SCROLL_THRESHOLD = Number(import.meta.env.VITE_VIRTUAL_SCROLL_THRESHOLD) || 100

export default function HomePage() {
  const navigate = useNavigate()
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
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  const handleView = (agentId: string) => {
    navigate(`/agents/${agentId}`)
  }

  const handleDelete = (agentId: string) => {
    console.log('Delete agent:', agentId)
  }

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
            <h1 className="text-3xl md:text-4xl font-bold text-gray-800">Agents</h1>
            <p className="text-sm md:text-base text-gray-600 mt-1">
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
            <h1 className="text-3xl md:text-4xl font-bold text-gray-800">Agents</h1>
            <p className="text-sm md:text-base text-gray-600 mt-1">
              Dynamic Taxonomy RAG System
            </p>
          </div>
        </header>
        <div className="text-center py-12">
          <p className="text-red-600 text-lg mb-4">
            Error: {error.message}
          </p>
          <p className="text-gray-600 mb-6">
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

  if (agents.length === 0) {
    return (
      <main className="p-8">
        <header className="flex items-center gap-6 mb-8">
          <img
            src="/company-logo.jpg"
            alt="Company Logo"
            className="h-16 md:h-20 w-auto object-contain rounded-lg shadow-md"
          />
          <div className="flex-1">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-800">Agents</h1>
            <p className="text-sm md:text-base text-gray-600 mt-1">
              Dynamic Taxonomy RAG System
            </p>
          </div>
        </header>
        <div className="text-center py-12">
          <p className="text-gray-600 text-lg">
            No agents found. Create your first agent to get started.
          </p>
        </div>
      </main>
    )
  }

  const useVirtualScroll = agents.length > VIRTUAL_SCROLL_THRESHOLD
  const columnCount = Math.floor(dimensions.width / 320) || 1
  const columnWidth = 320
  const rowHeight = 450

  return (
    <main className="p-8">
      {/* Header with Logo */}
      <header className="flex items-center gap-6 mb-8">
        <img
          src="/company-logo.jpg"
          alt="Company Logo"
          className="h-16 md:h-20 w-auto object-contain rounded-lg shadow-md"
        />
        <div className="flex-1">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-800">
            Agents {agents.length > 0 && `(${agents.length})`}
          </h1>
          <p className="text-sm md:text-base text-gray-600 mt-1">
            Dynamic Taxonomy RAG System
          </p>
        </div>
      </header>

      {useVirtualScroll ? (
        <div className="flex justify-center">
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
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
    </main>
  )
}
