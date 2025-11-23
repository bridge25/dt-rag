"use client"

/**
 * RecommendationPanel Component - contextual recommendations for users
 * @CODE:FRONTEND-MIGRATION-001
 */

import { Lightbulb, Plus, BookOpen } from "lucide-react"

interface RecommendationPanelProps {
  hasAgents: boolean
  onCreateAgent?: () => void
}

export function RecommendationPanel({
  hasAgents,
  onCreateAgent,
}: RecommendationPanelProps) {
  if (!hasAgents) {
    return (
      <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <Lightbulb className="w-6 h-6 text-blue-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              Get Started
            </h3>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start gap-2">
                <Plus className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <span>
                  Create your first agent to start building your knowledge base
                </span>
              </li>
              <li className="flex items-start gap-2">
                <BookOpen className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <span>
                  Upload documents to build your taxonomy and train agents
                </span>
              </li>
            </ul>
            {onCreateAgent && (
              <button
                onClick={onCreateAgent}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                Create Your First Agent
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-purple-50 rounded-lg border border-purple-200 p-6">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0">
          <Lightbulb className="w-6 h-6 text-purple-600" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">
            Recommended Actions
          </h3>
          <ul className="space-y-2 text-sm text-gray-700">
            <li>• Upload more documents to expand your knowledge base</li>
            <li>• Chat with your agents to help them level up</li>
            <li>• Review taxonomy structure for better organization</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
