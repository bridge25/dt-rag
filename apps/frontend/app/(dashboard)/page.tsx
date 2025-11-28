/**
 * Mission Control Dashboard
 * Ethereal Glass Aesthetic with redesigned welcome section
 *
 * @CODE:FRONTEND-REDESIGN-001-DASHBOARD
 */

"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
  Activity,
  Users,
  FileText,
  MessageSquare,
  Plus,
  ArrowUpRight,
  Cpu,
  Zap,
  Clock,
  Sparkles
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useAgents } from "@/hooks/useAgents"
import { GlassCard } from "@/components/ui/glass-card"
import { AgentCard } from "@/components/agent-card/AgentCard"
import type { AgentCardData } from "@/components/agent-card/types"

export default function HomePage() {
  const router = useRouter()
  const { agents, isLoading } = useAgents()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null

  const handleViewAgent = (agent: AgentCardData) => {
    router.push(`/agents/${agent.agent_id}`)
  }

  const _handleDeleteAgent = (agent: AgentCardData) => {
    console.log("Delete agent:", agent.agent_id)
  }

  // Ethereal Glass Theme: 시안 네온 글로우 중심으로 통일
  const stats = [
    {
      label: "System Health",
      value: "98.5%",
      trend: "+0.5%",
      icon: Activity,
      color: "text-cyan-400",
      glow: "shadow-[0_0_15px_rgba(0,247,255,0.3)]"
    },
    {
      label: "Active Agents",
      value: agents.length.toString(),
      trend: "+2",
      icon: Users,
      color: "text-cyan-400",
      glow: "shadow-[0_0_15px_rgba(0,247,255,0.3)]"
    },
    {
      label: "Documents Processed",
      value: "12,450",
      trend: "+150",
      icon: FileText,
      color: "text-purple-400",
      glow: "shadow-[0_0_15px_rgba(188,19,254,0.3)]"
    },
    {
      label: "Total Queries",
      value: "45.2k",
      trend: "+1.2k",
      icon: MessageSquare,
      color: "text-amber-400",
      glow: "shadow-[0_0_15px_rgba(251,191,36,0.3)]"
    },
  ];

  const recentActivity = [
    { id: 1, type: "query", message: "Agent 'Research Bot' processed a complex query", time: "2 min ago", icon: Zap },
    { id: 2, type: "system", message: "System optimization completed successfully", time: "15 min ago", icon: Cpu },
    { id: 3, type: "upload", message: "New document batch uploaded to 'Legal Docs'", time: "1 hour ago", icon: FileText },
    { id: 4, type: "agent", message: "New agent 'Support Assistant' created", time: "3 hours ago", icon: Plus },
  ];

  return (
    <main className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-amber-400" />
            Mission Control
          </h1>
          <p className="text-white/60 mt-1">System Overview & Status</p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => router.push("/agents")}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 border border-blue-500/30 rounded-lg transition-all duration-300 hover:shadow-[0_0_15px_rgba(59,130,246,0.3)]"
          >
            <Plus className="w-4 h-4" />
            View All Agents
          </button>
        </div>
      </div>

      {/* Welcome Section */}
      <GlassCard className="p-8 bg-gradient-to-r from-cyan-500/5 to-purple-500/5 border border-cyan-500/20 mb-8">
        <div className="flex items-start gap-6">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-white mb-2">Welcome to Ethereal Glass UI</h2>
            <p className="text-white/70 mb-4">
              Your specialized AI workforce with redesigned Ethereal Glass aesthetics. Manage agents, explore taxonomies, and monitor system performance in real-time.
            </p>
            <div className="flex items-center gap-3 text-sm">
              <span className="flex items-center gap-1 text-cyan-300">
                <Sparkles className="w-4 h-4" /> {agents.length} Active Agents
              </span>
              <span className="text-white/40">•</span>
              <span className="flex items-center gap-1 text-cyan-300">
                <Activity className="w-4 h-4" /> System Healthy
              </span>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Stats Grid - Ethereal Glass with Neon Glow */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div
            key={index}
            className={cn(
              "group relative overflow-hidden rounded-2xl p-6",
              // Glass morphism
              "bg-white/5 backdrop-blur-lg border border-white/10",
              // Hover: 시안 네온 글로우 강화
              "transition-all duration-300",
              "hover:bg-white/10 hover:border-cyan-400/30",
              "hover:shadow-[0_0_25px_rgba(0,247,255,0.4)]"
            )}
          >
            {/* Ambient glow background */}
            <div className={cn("absolute -right-6 -top-6 h-24 w-24 rounded-full opacity-30 blur-2xl transition-all group-hover:opacity-50", stat.color.replace("text-", "bg-"))} />

            <div className="flex items-start justify-between relative z-10">
              <div className={cn("p-3 rounded-xl bg-white/5 border border-white/10", stat.color, stat.glow)}>
                <stat.icon className="w-6 h-6 drop-shadow-[0_0_8px_currentColor]" />
              </div>
              <div className="flex items-center gap-1 text-sm font-medium text-cyan-400 bg-cyan-400/10 px-2 py-1 rounded-full border border-cyan-400/20">
                <ArrowUpRight className="w-3 h-3" />
                {stat.trend}
              </div>
            </div>

            <div className="mt-4 relative z-10">
              <h3 className={cn("text-3xl font-bold tracking-tight", stat.color, "drop-shadow-[0_0_10px_currentColor]")}>{stat.value}</h3>
              <p className="text-sm text-white/60 mt-1">{stat.label}</p>
            </div>

            {/* Bottom glow bar on hover */}
            <div className="absolute bottom-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Active Agents Column with AgentCardGrid */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-white">Featured Agents</h2>
            <button
              onClick={() => router.push("/agents")}
              className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
            >
              View All
            </button>
          </div>

          {isLoading ? (
            // Loading Skeletons
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="aspect-[3/4] rounded-2xl bg-white/5 animate-pulse border border-white/10" />
              ))}
            </div>
          ) : agents.length > 0 ? (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {agents.slice(0, 4).map((agent) => (
                <div
                  key={agent.agent_id}
                  onClick={() => handleViewAgent(agent)}
                  className="cursor-pointer"
                >
                  <AgentCard agent={agent} />
                </div>
              ))}
            </div>
          ) : (
            <GlassCard className="text-center py-8">
              <p className="text-gray-400">No agents available yet</p>
            </GlassCard>
          )}
        </div>

        {/* Recent Activity Column - Ethereal Glass */}
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-white">Recent Activity</h2>
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-lg p-6 space-y-6 hover:border-cyan-400/20 transition-colors duration-300">
            {recentActivity.map((item) => (
              <div key={item.id} className="relative pl-6 border-l border-cyan-400/20 last:border-0 pb-6 last:pb-0">
                <div className="absolute -left-1.5 top-0 h-3 w-3 rounded-full bg-cyan-400 shadow-[0_0_10px_rgba(0,247,255,0.6)]" />
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-white/40 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {item.time}
                  </span>
                  <p className="text-sm text-white/80">{item.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
