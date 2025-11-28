/**
 * Level Up Timeline Component
 * Displays the agent's level up history
 *
 * @CODE:FRONTEND-MIGRATION-002:TIMELINE
 */
"use client"

import type { AgentCardData } from "@/lib/api/types"

interface LevelUpTimelineProps {
  agent: AgentCardData
}

interface LevelEvent {
  level: number
  date: string
  xp: number
}

export function LevelUpTimeline({ agent }: LevelUpTimelineProps) {
  // Generate level events based on current level
  const agentLevel = agent.level ?? 1
  const events: LevelEvent[] = Array.from({ length: agentLevel }, (_, i) => ({
    level: i + 1,
    date: agent.created_at ?? new Date().toISOString(),
    xp: i * 100,
  }))

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Level Up History</h2>

      <div className="space-y-4">
        {events.reverse().map((event) => (
          <div
            key={event.level}
            className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <div className="flex-shrink-0 w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-xl">{event.level}</span>
            </div>

            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <h3 className="text-lg font-semibold text-gray-900">
                  Level {event.level} Achieved
                </h3>
                <span className="text-sm text-gray-500">
                  {new Date(event.date).toLocaleDateString()}
                </span>
              </div>
              <p className="text-sm text-gray-600">{event.xp} XP earned</p>
            </div>
          </div>
        ))}
      </div>

      {events.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No level up events yet
        </div>
      )}
    </div>
  )
}
