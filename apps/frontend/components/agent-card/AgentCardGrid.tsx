/**
 * AgentCardGrid Component
 * Responsive grid layout for displaying agent cards with staggered animation
 *
 * @CODE:AGENT-CARD-GRID-IMPL-001
 */

"use client"

import React, { memo } from "react"
import { cn } from "@/lib/utils"
import { AgentCard } from "./AgentCard"
import type { AgentCardData } from "./types"

interface AgentCardGridProps {
  agents: AgentCardData[]
  onView: (agent: AgentCardData) => void
  onDelete: (agent: AgentCardData) => void
  className?: string
}

const AgentCardGridComponent = React.forwardRef<
  HTMLDivElement,
  AgentCardGridProps
>(({ agents, onView, onDelete, className }, ref) => {
  const isEmpty = agents.length === 0

  return (
    <section
      ref={ref}
      aria-label="Agent cards grid"
      className={cn(
        "w-full",
        className
      )}
    >
      {isEmpty ? (
        // Empty state
        <div className="flex flex-col items-center justify-center py-16 px-4">
          <div className="text-center max-w-md">
            <h3 className="text-xl font-semibold text-white mb-2">
              No agents yet
            </h3>
            <p className="text-gray-400 text-sm">
              Create or import agents to get started. Each agent will appear here
              with their stats, progress, and management options.
            </p>
          </div>
        </div>
      ) : (
        // Agent cards grid
        <div
          className={cn(
            "grid",
            "grid-cols-1",
            "sm:grid-cols-2",
            "lg:grid-cols-3",
            "xl:grid-cols-4",
            "gap-4",
            "w-full"
          )}
        >
          {agents.map((agent, index) => {
            const itemId = `agent-card-${agent.agent_id}`
            return (
              <div
                key={agent.agent_id}
                data-testid={itemId}
                data-agent-name={agent.name}
                className={cn(
                  "animate-in fade-in zoom-in",
                  "transition-all duration-500 ease-out"
                )}
                style={{
                  animation: `fadeInZoom 0.5s ease-out ${index * 50}ms forwards`,
                  opacity: 0,
                }}
              >
                <AgentCard
                  agent={agent}
                  onView={() => onView(agent)}
                  onDelete={() => onDelete(agent)}
                />
              </div>
            )
          })}
        </div>
      )}

      <style>{`
        @keyframes fadeInZoom {
          from {
            opacity: 0;
            transform: scale(0.95) translateY(10px);
          }
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
      `}</style>
    </section>
  )
})

AgentCardGridComponent.displayName = "AgentCardGrid"

// Memoized version for performance optimization
const arePropsEqual = (
  prevProps: AgentCardGridProps,
  nextProps: AgentCardGridProps
) => {
  // Check if agent list length changed
  if (prevProps.agents.length !== nextProps.agents.length) {
    return false
  }

  // Check if agent IDs are the same
  const prevIds = prevProps.agents.map((a) => a.agent_id).join(",")
  const nextIds = nextProps.agents.map((a) => a.agent_id).join(",")

  return (
    prevIds === nextIds &&
    prevProps.className === nextProps.className
  )
}

export const AgentCardGrid = memo(AgentCardGridComponent, arePropsEqual)
