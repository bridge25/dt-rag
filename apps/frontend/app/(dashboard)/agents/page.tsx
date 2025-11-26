/**
 * Agents page for managing AI agents and their performance metrics
 * Ethereal Glass Aesthetic
 *
 * @CODE:FRONTEND-002
 */

"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  listAgents,
  createAgentFromCategory,
  deleteAgent,
  getAgentMetrics,
  type AgentStatus,
  type AgentMetrics,
  type FromCategoryRequest
} from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import {
  Bot,
  Plus,
  Activity,
  CheckCircle2,
  XCircle,
  Trash2,
  BarChart3,
  RefreshCw,
  Search,
  Zap,
  Cpu,
  MoreVertical
} from "lucide-react"
import { cn } from "@/lib/utils"

export default function AgentsPage() {
  const [selectedAgent, setSelectedAgent] = useState<AgentStatus | null>(null)
  const [metricsData, setMetricsData] = useState<AgentMetrics | null>(null)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [categoryPath, setCategoryPath] = useState("")
  const queryClient = useQueryClient()

  const { data: agentsData, isLoading, isError } = useQuery({
    queryKey: ["agents"],
    queryFn: () => listAgents(),
    refetchInterval: 30000,
  })

  const createMutation = useMutation({
    mutationFn: createAgentFromCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
      setIsCreateDialogOpen(false)
      setCategoryPath("")
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
      setSelectedAgent(null)
    },
  })

  const loadMetrics = async (agentId: string) => {
    try {
      const metrics = await getAgentMetrics(agentId)
      setMetricsData(metrics)
    } catch (error) {
      console.error("Failed to load metrics:", error)
    }
  }

  const handleCreateAgent = () => {
    const paths = categoryPath.split(",").map(p => p.trim()).filter(Boolean)
    if (paths.length === 0) {
      alert("Please enter at least one category path")
      return
    }

    const request: FromCategoryRequest = {
      category_path: paths,
      config: {},
      features: {
        semantic_search: true,
        keyword_search: true,
        classification: true,
      }
    }
    createMutation.mutate(request)
  }

  return (
    <div className="space-y-8 p-8 max-w-7xl mx-auto">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">AI Agents</h1>
          <p className="mt-1 text-white/60">
            Manage and monitor your specialized AI workforce
          </p>
        </div>

        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <button className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 border border-blue-500/30 rounded-lg transition-all duration-300 hover:shadow-[0_0_15px_rgba(59,130,246,0.3)]">
              <Plus className="w-4 h-4" />
              Create Agent
            </button>
          </DialogTrigger>
          <DialogContent className="bg-dark-navy/95 border-white/10 backdrop-blur-xl text-white sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold">Create Agent from Category</DialogTitle>
              <DialogDescription className="text-white/60">
                Enter taxonomy category paths to spawn a specialized agent.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="categoryPath" className="text-white/80">Category Path(s)</Label>
                <Input
                  id="categoryPath"
                  value={categoryPath}
                  onChange={(e) => setCategoryPath(e.target.value)}
                  placeholder="Technology, Science, Business"
                  className="bg-white/5 border-white/10 text-white placeholder:text-white/30 focus:border-blue-500/50 focus:ring-blue-500/20"
                />
                <p className="text-xs text-white/40">
                  Comma-separated paths, e.g., "Technology, AI"
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="ghost"
                onClick={() => setIsCreateDialogOpen(false)}
                className="text-white/60 hover:text-white hover:bg-white/5"
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreateAgent}
                disabled={createMutation.isPending}
                className="bg-blue-600 hover:bg-blue-500 text-white"
              >
                {createMutation.isPending ? "Creating..." : "Create Agent"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Overview */}
      {agentsData && (
        <div className="grid gap-6 md:grid-cols-3">
          <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md group hover:bg-white/10 transition-all duration-300">
            <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-blue-500/20 blur-2xl group-hover:bg-blue-500/30 transition-all" />
            <div className="flex items-center justify-between relative z-10">
              <div>
                <p className="text-sm font-medium text-white/60">Total Agents</p>
                <p className="text-4xl font-bold mt-2 text-white">{agentsData.total}</p>
              </div>
              <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
                <Bot className="w-6 h-6" />
              </div>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md group hover:bg-white/10 transition-all duration-300">
            <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-green-500/20 blur-2xl group-hover:bg-green-500/30 transition-all" />
            <div className="flex items-center justify-between relative z-10">
              <div>
                <p className="text-sm font-medium text-white/60">Active</p>
                <p className="text-4xl font-bold mt-2 text-white">{agentsData.active}</p>
              </div>
              <div className="p-3 rounded-xl bg-green-500/10 border border-green-500/20 text-green-400">
                <Activity className="w-6 h-6" />
              </div>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md group hover:bg-white/10 transition-all duration-300">
            <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-orange-500/20 blur-2xl group-hover:bg-orange-500/30 transition-all" />
            <div className="flex items-center justify-between relative z-10">
              <div>
                <p className="text-sm font-medium text-white/60">Inactive</p>
                <p className="text-4xl font-bold mt-2 text-white">{agentsData.inactive}</p>
              </div>
              <div className="p-3 rounded-xl bg-orange-500/10 border border-orange-500/20 text-orange-400">
                <XCircle className="w-6 h-6" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm">
          <RefreshCw className="h-12 w-12 text-blue-400 animate-spin mb-4" />
          <p className="text-lg font-medium text-white/80">Initializing Agent Network...</p>
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 backdrop-blur-sm flex items-center gap-4">
          <XCircle className="h-8 w-8 text-red-400" />
          <div>
            <h3 className="text-lg font-bold text-red-400">Connection Error</h3>
            <p className="text-white/60">Failed to synchronize with the agent network.</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {agentsData && agentsData.agents.length === 0 && (
        <div className="text-center py-20 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm">
          <div className="h-20 w-20 rounded-full bg-white/5 mx-auto flex items-center justify-center mb-6 border border-white/10">
            <Bot className="h-10 w-10 text-white/40" />
          </div>
          <h2 className="text-2xl font-bold mb-2 text-white">No Agents Deployed</h2>
          <p className="text-white/60 mb-8 max-w-md mx-auto">
            Your agent network is currently empty. Deploy your first agent to start processing data.
          </p>
          <Button
            onClick={() => setIsCreateDialogOpen(true)}
            className="bg-blue-600 hover:bg-blue-500 text-white"
          >
            <Plus className="mr-2 h-4 w-4" />
            Deploy First Agent
          </Button>
        </div>
      )}

      {/* Agents Grid */}
      {agentsData && agentsData.agents.length > 0 && (
        <div className="grid gap-6">
          {agentsData.agents.map((agent) => {
            const isSelected = selectedAgent?.agent_id === agent.agent_id

            return (
              <div
                key={agent.agent_id}
                className={cn(
                  "group relative overflow-hidden rounded-2xl border bg-white/5 backdrop-blur-md transition-all duration-300",
                  isSelected
                    ? "border-blue-500/50 bg-blue-500/5 shadow-[0_0_30px_rgba(59,130,246,0.1)]"
                    : "border-white/10 hover:bg-white/10 hover:border-white/20 hover:shadow-glass"
                )}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between gap-6">
                    {/* Icon & Status */}
                    <div className="flex items-start gap-4 flex-1">
                      <div className={cn(
                        "h-12 w-12 rounded-xl flex items-center justify-center border",
                        agent.status === "active"
                          ? "bg-green-500/10 border-green-500/20 text-green-400"
                          : "bg-red-500/10 border-red-500/20 text-red-400"
                      )}>
                        {agent.status === "active" ? <Activity className="w-6 h-6" /> : <XCircle className="w-6 h-6" />}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-xl font-bold text-white group-hover:text-blue-300 transition-colors">
                            {agent.name}
                          </h3>
                          <span className={cn(
                            "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
                            agent.status === "active"
                              ? "bg-green-500/10 border-green-500/20 text-green-400"
                              : "bg-red-500/10 border-red-500/20 text-red-400"
                          )}>
                            {agent.status.toUpperCase()}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-4">
                          <div>
                            <p className="text-xs text-white/40 uppercase tracking-wider">Agent ID</p>
                            <p className="text-sm font-mono text-white/80 truncate mt-1">
                              {agent.agent_id}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-white/40 uppercase tracking-wider">Created</p>
                            <p className="text-sm text-white/80 mt-1">
                              {new Date(agent.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-white/40 uppercase tracking-wider">Last Used</p>
                            <p className="text-sm text-white/80 mt-1">
                              {agent.last_used ? new Date(agent.last_used).toLocaleDateString() : "Never"}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-white/40 uppercase tracking-wider">Usage</p>
                            <p className="text-sm font-bold text-blue-400 mt-1">
                              {agent.usage_count} ops
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          if (isSelected) {
                            setSelectedAgent(null)
                            setMetricsData(null)
                          } else {
                            setSelectedAgent(agent)
                            loadMetrics(agent.agent_id)
                          }
                        }}
                        className={cn(
                          "border transition-all",
                          isSelected
                            ? "bg-blue-500/20 text-blue-300 border-blue-500/30"
                            : "bg-white/5 text-white/60 border-white/10 hover:bg-white/10 hover:text-white"
                        )}
                      >
                        <BarChart3 className="mr-2 h-4 w-4" />
                        {isSelected ? "Hide Metrics" : "View Metrics"}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          if (confirm(`Delete agent "${agent.name}"?`)) {
                            deleteMutation.mutate(agent.agent_id)
                          }
                        }}
                        disabled={deleteMutation.isPending}
                        className="bg-red-500/5 text-red-400/60 border border-red-500/10 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/30"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </Button>
                    </div>
                  </div>

                  {/* Expanded Metrics Section */}
                  {isSelected && metricsData && (
                    <div className="mt-8 pt-6 border-t border-white/10 animate-in fade-in slide-in-from-top-4 duration-300">
                      <div className="space-y-6">
                        <div className="flex items-center justify-between">
                          <h4 className="text-lg font-bold text-white flex items-center gap-2">
                            <Activity className="w-5 h-5 text-blue-400" />
                            Performance Analytics
                          </h4>
                          <span className="text-xs text-white/40">Real-time data</span>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="rounded-xl bg-white/5 border border-white/10 p-4 hover:bg-white/10 transition-colors">
                            <p className="text-xs text-white/40 uppercase tracking-wider mb-1">Total Requests</p>
                            <p className="text-2xl font-bold text-white">{metricsData.total_requests}</p>
                          </div>
                          <div className="rounded-xl bg-white/5 border border-white/10 p-4 hover:bg-white/10 transition-colors">
                            <p className="text-xs text-white/40 uppercase tracking-wider mb-1">Avg Latency</p>
                            <p className="text-2xl font-bold text-green-400">{metricsData.avg_response_time_ms.toFixed(0)}ms</p>
                          </div>
                          <div className="rounded-xl bg-white/5 border border-white/10 p-4 hover:bg-white/10 transition-colors">
                            <p className="text-xs text-white/40 uppercase tracking-wider mb-1">Success Rate</p>
                            <p className="text-2xl font-bold text-blue-400">{(metricsData.success_rate * 100).toFixed(1)}%</p>
                          </div>
                          <div className="rounded-xl bg-white/5 border border-white/10 p-4 hover:bg-white/10 transition-colors">
                            <p className="text-xs text-white/40 uppercase tracking-wider mb-1">Satisfaction</p>
                            <p className="text-2xl font-bold text-purple-400">{(metricsData.user_satisfaction * 100).toFixed(1)}%</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
