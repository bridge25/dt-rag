/**
 * Agents page - Ethereal Glass Design with AgentCardGrid Integration
 * Based on 뉴디자인1 concept with 3D robot avatars and glass cards
 *
 * @CODE:FRONTEND-REDESIGN-001-AGENTS-PAGE
 */

"use client"

import { useState, useCallback } from "react"
import { Plus, Search, Grid, List, Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAgents } from "@/hooks/useAgents"
import { AgentCardGrid } from "@/components/agent-card/AgentCardGrid"
import { GlassCard } from "@/components/ui/glass-card"
import type { AgentCardData } from "@/components/agent-card/types"

export default function AgentsPage() {
  const { agents, isLoading } = useAgents()
  const [searchQuery, setSearchQuery] = useState("")
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")

  // Filter agents by search query
  const filteredAgents = agents.filter(agent =>
    agent.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Handle agent view action
  const handleViewAgent = useCallback((agent: AgentCardData) => {
    // Navigate to agent detail page
    console.log("View agent:", agent.agent_id)
  }, [])

  // Handle agent delete action
  const handleDeleteAgent = useCallback((agent: AgentCardData) => {
    // Delete agent
    console.log("Delete agent:", agent.agent_id)
  }, [])

  // Calculate stats
  const totalAgents = agents.length
  const activeAgents = agents.filter(a => a.status === "active").length
  const totalQueries = agents.reduce((sum, a) => sum + (a.total_queries || 0), 0)
  const avgQuality = agents.length > 0
    ? Math.round(agents.reduce((sum, a) => sum + (a.quality_score || 0), 0) / agents.length)
    : 0

  return (
    <div className="min-h-screen p-8">
      {/* Animated background particles - subtle star effect */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-2 h-2 bg-white/20 rounded-full animate-pulse" />
        <div className="absolute top-40 right-40 w-1 h-1 bg-blue-400/30 rounded-full animate-pulse delay-100" />
        <div className="absolute top-60 left-1/3 w-1.5 h-1.5 bg-purple-400/20 rounded-full animate-pulse delay-200" />
        <div className="absolute bottom-40 right-20 w-1 h-1 bg-cyan-400/30 rounded-full animate-pulse delay-300" />
        <div className="absolute bottom-20 left-40 w-2 h-2 bg-amber-400/20 rounded-full animate-pulse delay-500" />
      </div>

      <div className="relative max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
              <Sparkles className="w-8 h-8 text-amber-400" />
              AI Agents
            </h1>
            <p className="mt-2 text-white/60">
              Your specialized AI workforce • {totalAgents} agents deployed
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search agents..."
                className="pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 w-64 transition-all"
              />
            </div>

            {/* View Toggle */}
            <div className="flex items-center gap-1 p-1 bg-white/5 rounded-lg border border-white/10">
              <button
                onClick={() => setViewMode("grid")}
                className={cn(
                  "p-2 rounded-md transition-all",
                  viewMode === "grid"
                    ? "bg-white/10 text-white"
                    : "text-white/40 hover:text-white/60"
                )}
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode("list")}
                className={cn(
                  "p-2 rounded-md transition-all",
                  viewMode === "list"
                    ? "bg-white/10 text-white"
                    : "text-white/40 hover:text-white/60"
                )}
              >
                <List className="w-4 h-4" />
              </button>
            </div>

            {/* Create Button */}
            <button className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-400 hover:to-cyan-400 text-white font-medium rounded-xl transition-all duration-300 hover:shadow-[0_0_25px_rgba(59,130,246,0.4)] hover:-translate-y-0.5">
              <Plus className="w-4 h-4" />
              New Agent
            </button>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Total Agents", value: totalAgents.toString(), icon: "🤖", color: "blue" },
            { label: "Active Now", value: activeAgents.toString(), icon: "⚡", color: "green" },
            { label: "Total Queries", value: totalQueries.toLocaleString(), icon: "📊", color: "purple" },
            { label: "Avg Quality", value: `${avgQuality}%`, icon: "⭐", color: "amber" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-md group hover:bg-white/10 transition-all duration-300"
            >
              <div className={cn(
                "absolute -right-4 -top-4 h-20 w-20 rounded-full blur-2xl transition-all",
                stat.color === "blue" && "bg-blue-500/20 group-hover:bg-blue-500/30",
                stat.color === "green" && "bg-green-500/20 group-hover:bg-green-500/30",
                stat.color === "purple" && "bg-purple-500/20 group-hover:bg-purple-500/30",
                stat.color === "amber" && "bg-amber-500/20 group-hover:bg-amber-500/30",
              )} />
              <div className="relative z-10 flex items-center gap-3">
                <span className="text-2xl">{stat.icon}</span>
                <div>
                  <p className="text-xs text-white/50 uppercase tracking-wider">{stat.label}</p>
                  <p className="text-2xl font-bold text-white mt-0.5">{stat.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Content based on view mode */}
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <div className="inline-flex p-4 rounded-full bg-white/5 border border-white/10 mb-4">
                <Sparkles className="w-8 h-8 text-cyan-400 animate-spin" />
              </div>
              <p className="text-white/60 animate-pulse">Loading agents...</p>
            </div>
          </div>
        ) : filteredAgents.length === 0 ? (
          <GlassCard className="text-center py-16">
            <Sparkles className="w-16 h-16 mx-auto mb-4 text-gray-500" />
            <h3 className="text-xl font-medium text-white mb-2">No agents found</h3>
            <p className="text-gray-400 mb-6">
              {searchQuery ? "Try adjusting your search query" : "Create your first agent to get started"}
            </p>
          </GlassCard>
        ) : (
          <div className={cn(
            "grid",
            viewMode === "grid"
              ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
              : "grid-cols-1"
          )}>
            <AgentCardGrid
              agents={filteredAgents}
              onView={handleViewAgent}
              onDelete={handleDeleteAgent}
            />
          </div>
        )}
      </div>
    </div>
  )
}
