// @CODE:AGENT-CARD-001-PAGE-001
'use client'

import { useAgents } from '../hooks/useAgents'
import { AgentCard } from '../components/agent-card/AgentCard'

export default function HomePage() {
  const { agents, isLoading, error, refetch } = useAgents()

  const handleView = (agentId: string) => {
    console.log('View agent:', agentId)
  }

  const handleDelete = (agentId: string) => {
    console.log('Delete agent:', agentId)
  }

  if (isLoading) {
    return (
      <main className="p-8">
        <h1 className="text-3xl font-bold mb-8">Agents</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, index) => (
            <div
              key={index}
              className="h-96 bg-gray-200 rounded-lg animate-pulse"
            />
          ))}
        </div>
        <p className="text-center text-gray-600 mt-8">Loading agents...</p>
      </main>
    )
  }

  if (error) {
    return (
      <main className="p-8">
        <h1 className="text-3xl font-bold mb-8">Agents</h1>
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
        <h1 className="text-3xl font-bold mb-8">Agents</h1>
        <div className="text-center py-12">
          <p className="text-gray-600 text-lg">
            No agents found. Create your first agent to get started.
          </p>
        </div>
      </main>
    )
  }

  return (
    <main className="p-8">
      <h1 className="text-3xl font-bold mb-8">Agents</h1>
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
    </main>
  )
}
