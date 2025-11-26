/**
 * Mission Control Dashboard
 * Ethereal Glass Aesthetic
 *
 * @CODE:FRONTEND-002
 */

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  Users,
  FileText,
  MessageSquare,
  Plus,
  ArrowUpRight,
  Cpu,
  Zap,
  Clock
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAgents } from "@/hooks/useAgents";

export default function HomePage() {
  const router = useRouter();
  const { agents, isLoading } = useAgents();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const stats = [
    {
      label: "System Health",
      value: "98.5%",
      trend: "+0.5%",
      icon: Activity,
      color: "text-green-400",
      glow: "shadow-[0_0_20px_rgba(74,222,128,0.2)]"
    },
    {
      label: "Active Agents",
      value: agents.length.toString(),
      trend: "+2",
      icon: Users,
      color: "text-blue-400",
      glow: "shadow-[0_0_20px_rgba(96,165,250,0.2)]"
    },
    {
      label: "Documents Processed",
      value: "12,450",
      trend: "+150",
      icon: FileText,
      color: "text-purple-400",
      glow: "shadow-[0_0_20px_rgba(192,132,252,0.2)]"
    },
    {
      label: "Total Queries",
      value: "45.2k",
      trend: "+1.2k",
      icon: MessageSquare,
      color: "text-orange-400",
      glow: "shadow-[0_0_20px_rgba(251,146,60,0.2)]"
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
          <h1 className="text-3xl font-bold text-white tracking-tight">Mission Control</h1>
          <p className="text-white/60 mt-1">System Overview & Status</p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => router.push("/agents/create")}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 border border-blue-500/30 rounded-lg transition-all duration-300 hover:shadow-[0_0_15px_rgba(59,130,246,0.3)]"
          >
            <Plus className="w-4 h-4" />
            New Agent
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div
            key={index}
            className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md transition-all duration-300 hover:bg-white/10 hover:border-white/20"
          >
            <div className={cn("absolute -right-6 -top-6 h-24 w-24 rounded-full opacity-20 blur-2xl transition-all group-hover:opacity-40", stat.color.replace("text-", "bg-"))} />

            <div className="flex items-start justify-between">
              <div className={cn("p-3 rounded-xl bg-white/5 border border-white/10", stat.color, stat.glow)}>
                <stat.icon className="w-6 h-6" />
              </div>
              <div className="flex items-center gap-1 text-sm font-medium text-green-400 bg-green-400/10 px-2 py-1 rounded-full border border-green-400/20">
                <ArrowUpRight className="w-3 h-3" />
                {stat.trend}
              </div>
            </div>

            <div className="mt-4">
              <h3 className="text-3xl font-bold text-white tracking-tight">{stat.value}</h3>
              <p className="text-sm text-white/60 mt-1">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Active Agents Column */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-white">Active Agents</h2>
            <button
              onClick={() => router.push("/agents")}
              className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
            >
              View All
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {isLoading ? (
              // Loading Skeletons
              [...Array(4)].map((_, i) => (
                <div key={i} className="h-32 rounded-2xl bg-white/5 animate-pulse border border-white/10" />
              ))
            ) : agents.slice(0, 4).map((agent) => (
              <div
                key={agent.agent_id}
                onClick={() => router.push(`/agents/${agent.agent_id}`)}
                className="group cursor-pointer rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm transition-all duration-300 hover:bg-white/10 hover:border-blue-500/30 hover:shadow-glass hover:-translate-y-1"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/10 flex items-center justify-center">
                    <Users className="w-5 h-5 text-blue-300" />
                  </div>
                  <div className="px-2 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-xs text-green-400">
                    Active
                  </div>
                </div>
                <h3 className="font-semibold text-white group-hover:text-blue-300 transition-colors">{agent.name}</h3>
                <p className="text-sm text-white/50 mt-1 line-clamp-2">{agent.character_description || "No description provided."}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity Column */}
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-white">Recent Activity</h2>
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 space-y-6">
            {recentActivity.map((item) => (
              <div key={item.id} className="relative pl-6 border-l border-white/10 last:border-0 pb-6 last:pb-0">
                <div className="absolute -left-1.5 top-0 h-3 w-3 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
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
