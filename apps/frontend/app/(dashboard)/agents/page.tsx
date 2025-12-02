/**
 * Agents page - Ethereal Glass Design with AgentCardGrid Integration
 * Matches 뉴디자인1 (Ethereal Glass Design) with 5-column grid layout
 *
 * @CODE:FRONTEND-REDESIGN-001-AGENTS-PAGE
 */

"use client"

import { useState } from "react"
import { Plus, Search, Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAgents } from "@/hooks/useAgents"
import { AgentCardGrid } from "@/components/agent-card/AgentCardGrid"

export default function AgentsPage() {
  const { agents, isLoading } = useAgents()
  const [searchQuery, setSearchQuery] = useState("")

  // Filter agents by search query
  const filteredAgents = agents.filter(agent =>
    agent.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Calculate stats from agents
  const totalAgents = agents.length
  const activeAgents = agents.filter(a => a.status === "active").length
  const totalUsers = agents.reduce((sum, a) => sum + (a.stats?.users || 0), 0)
  const _totalRevenue = agents.reduce((sum, a) => sum + (a.stats?.revenue || 0), 0)
  const avgGrowth = agents.length > 0
    ? Math.round(agents.reduce((sum, a) => sum + (a.stats?.growth || 0), 0) / agents.length)
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
              {/* Gemini Guide: 아이콘 네온 글로우 */}
              <Sparkles className="w-8 h-8 text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.7)]" />
              AI Agents
            </h1>
            <p className="mt-2 text-white/60">
              Your specialized AI workforce • {totalAgents} agents deployed
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Search - Gemini Guide: rounded-full, 유리 질감 */}
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search agents..."
                className="pl-11 pr-4 py-2.5 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full text-white placeholder:text-white/40 focus:outline-none focus:border-cyan-400/50 focus:ring-2 focus:ring-cyan-400/20 w-64 transition-all"
              />
            </div>

            {/* Create Button - Gemini Guide: 네온 글로우 강화 */}
            <button className={cn(
              "flex items-center gap-2 px-6 py-2.5 rounded-full",
              "bg-cyan-600/30 border border-cyan-400",
              "text-white font-semibold",
              "shadow-[0_0_12px_rgba(0,247,255,0.6)]",
              "transition-all duration-300",
              "hover:bg-cyan-500/50 hover:shadow-[0_0_20px_rgba(0,247,255,0.9)]",
              "hover:-translate-y-0.5"
            )}>
              <Plus className="w-4 h-4" />
              New Agent
            </button>
          </div>
        </div>

        {/* Stats Overview - Gemini Guide: bg-white/10 (더 불투명), 네온 글로우 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Total Agents", value: totalAgents.toString(), icon: "🤖", color: "cyan" },
            { label: "Active Now", value: activeAgents.toString(), icon: "⚡", color: "cyan" },
            { label: "Total Users", value: totalUsers.toLocaleString(), icon: "👥", color: "cyan" },
            { label: "Avg Growth", value: `${avgGrowth}%`, icon: "📈", color: "cyan" },
          ].map((stat) => (
            <div
              key={stat.label}
              className={cn(
                "relative overflow-hidden rounded-xl p-5",
                // Gemini Guide: bg-white/10 backdrop-blur-md border-white/20
                "bg-white/10 backdrop-blur-md border border-white/20",
                "shadow-md group",
                "transition-all duration-300",
                // Hover: 네온 글로우
                "hover:border-cyan-400/50",
                "hover:shadow-[0_4px_20px_rgba(0,0,0,0.3),_0_0_15px_rgba(0,247,255,0.5)]"
              )}
            >
              <div className={cn(
                "absolute -right-4 -top-4 h-20 w-20 rounded-full blur-2xl transition-all",
                "bg-cyan-500/20 group-hover:bg-cyan-500/40"
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

        {/* Content area */}
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
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <Sparkles className="w-16 h-16 mx-auto mb-4 text-gray-500" />
            <h3 className="text-xl font-medium text-white mb-2">No agents found</h3>
            <p className="text-gray-400 mb-6">
              {searchQuery ? "Try adjusting your search query" : "Create your first agent to get started"}
            </p>
          </div>
        ) : (
          <AgentCardGrid agents={filteredAgents} />
        )}
      </div>
    </div>
  )
}
