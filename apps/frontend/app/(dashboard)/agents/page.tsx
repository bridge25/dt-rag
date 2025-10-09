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
import { ModernCard } from "@/components/ui/modern-card"
import { IconBadge } from "@/components/ui/icon-badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Bot, Plus, Activity, CheckCircle2, XCircle, Trash2, BarChart3, RefreshCw } from "lucide-react"

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
    <div className="space-y-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-6">
      <ModernCard variant="dark">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <IconBadge icon={Bot} color="teal" size="lg" />
            <div>
              <h1 className="text-3xl font-bold">AI Agents</h1>
              <p className="mt-1 text-sm text-white/80">
                Manage specialized AI agents for your taxonomy categories
              </p>
            </div>
          </div>

          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-tealAccent hover:bg-tealAccent/90 text-gray-900">
                <Plus className="mr-2 h-4 w-4" />
                Create Agent
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Create Agent from Category</DialogTitle>
                <DialogDescription>
                  Enter taxonomy category paths (comma-separated) to create a specialized agent
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="categoryPath">Category Path(s)</Label>
                  <Input
                    id="categoryPath"
                    value={categoryPath}
                    onChange={(e) => setCategoryPath(e.target.value)}
                    placeholder="Technology, Science, Business"
                  />
                  <p className="text-xs text-muted-foreground">
                    Example: Technology, Science, Business
                  </p>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateAgent}
                  disabled={createMutation.isPending}
                  className="bg-purpleFolder hover:bg-purpleFolder/90 text-white"
                >
                  {createMutation.isPending ? "Creating..." : "Create Agent"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </ModernCard>

      {agentsData && (
        <div className="grid gap-4 md:grid-cols-3">
          <ModernCard variant="purple">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white/80">Total Agents</p>
                <p className="text-4xl font-bold mt-2">{agentsData.total}</p>
              </div>
              <IconBadge icon={Bot} color="orange" size="lg" />
            </div>
          </ModernCard>

          <ModernCard variant="green">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white/80">Active</p>
                <p className="text-4xl font-bold mt-2">{agentsData.active}</p>
              </div>
              <IconBadge icon={CheckCircle2} color="teal" size="lg" />
            </div>
          </ModernCard>

          <ModernCard variant="beige">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">Inactive</p>
                <p className="text-4xl font-bold mt-2 text-gray-900">{agentsData.inactive}</p>
              </div>
              <IconBadge icon={XCircle} color="red" size="lg" />
            </div>
          </ModernCard>
        </div>
      )}

      {isLoading && (
        <ModernCard variant="beige">
          <div className="flex flex-col items-center justify-center py-12">
            <RefreshCw className="h-12 w-12 text-orangePrimary animate-spin mb-4" />
            <p className="text-lg font-medium text-gray-700">Loading agents...</p>
          </div>
        </ModernCard>
      )}

      {isError && (
        <ModernCard variant="default" className="border-red-500 border-2">
          <div className="flex items-center gap-3">
            <IconBadge icon={XCircle} color="red" />
            <div>
              <h3 className="text-lg font-bold text-red-600">Error</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Failed to load agents
              </p>
            </div>
          </div>
        </ModernCard>
      )}

      {agentsData && agentsData.agents.length === 0 && (
        <ModernCard variant="teal">
          <div className="text-center py-12">
            <IconBadge icon={Bot} color="purple" size="lg" className="mx-auto mb-4" />
            <h2 className="text-3xl font-bold mb-2 text-gray-900">No Agents Yet</h2>
            <p className="text-lg text-gray-700 mb-4">Create your first AI agent to get started</p>
            <Button
              onClick={() => setIsCreateDialogOpen(true)}
              className="bg-purpleFolder hover:bg-purpleFolder/90 text-white"
            >
              <Plus className="mr-2 h-4 w-4" />
              Create Your First Agent
            </Button>
          </div>
        </ModernCard>
      )}

      {agentsData && agentsData.agents.length > 0 && (
        <div className="grid gap-4">
          {agentsData.agents.map((agent, index) => {
            const isSelected = selectedAgent?.agent_id === agent.agent_id
            const variant = index % 3 === 0 ? "purple" : index % 3 === 1 ? "green" : "teal"

            return (
              <ModernCard
                key={agent.agent_id}
                variant={isSelected ? "teal" : "default"}
                className={`transition-all duration-300 ${isSelected ? "ring-4 ring-tealAccent/30" : "hover:shadow-card"}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4 flex-1">
                    <IconBadge
                      icon={agent.status === "active" ? Activity : XCircle}
                      color={agent.status === "active" ? "green" : "red"}
                      size="md"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                          {agent.name}
                        </h3>
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold ${
                          agent.status === "active"
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-100 text-gray-800"
                        }`}>
                          {agent.status.toUpperCase()}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-4 mt-4">
                        <div>
                          <p className="text-xs text-muted-foreground">Agent ID</p>
                          <p className="text-sm font-mono text-gray-700 dark:text-gray-300 truncate">
                            {agent.agent_id}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Created</p>
                          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            {new Date(agent.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Last Used</p>
                          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            {agent.last_used ? new Date(agent.last_used).toLocaleDateString() : "Never"}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Usage Count</p>
                          <p className="text-sm font-bold text-orangePrimary">
                            {agent.usage_count}
                          </p>
                        </div>
                      </div>

                      {agent.performance_metrics && Object.keys(agent.performance_metrics).length > 0 && (
                        <div className="mt-4 p-4 rounded-xl bg-gray-100 dark:bg-gray-800">
                          <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">
                            Performance Metrics
                          </p>
                          <div className="grid grid-cols-3 gap-2">
                            {Object.entries(agent.performance_metrics).map(([key, value]) => (
                              <div key={key} className="text-center">
                                <p className="text-xs text-muted-foreground">{key}</p>
                                <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                                  {typeof value === "number" ? value.toFixed(2) : value}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {isSelected && metricsData && (
                        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                          <div className="space-y-4">
                            <h4 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                              Detailed Metrics
                            </h4>
                            <div className="grid grid-cols-2 gap-4">
                              <div className="rounded-xl bg-purple-50 dark:bg-purple-900/20 p-4">
                                <p className="text-sm text-gray-700 dark:text-gray-300 mb-1">Total Requests</p>
                                <p className="text-3xl font-bold text-purpleFolder">{metricsData.total_requests}</p>
                              </div>
                              <div className="rounded-xl bg-green-50 dark:bg-green-900/20 p-4">
                                <p className="text-sm text-gray-700 dark:text-gray-300 mb-1">Avg Response Time</p>
                                <p className="text-3xl font-bold text-greenFolder">{metricsData.avg_response_time_ms.toFixed(0)}ms</p>
                              </div>
                              <div className="rounded-xl bg-teal-50 dark:bg-teal-900/20 p-4">
                                <p className="text-sm text-gray-700 dark:text-gray-300 mb-1">Success Rate</p>
                                <p className="text-3xl font-bold text-tealAccent">{(metricsData.success_rate * 100).toFixed(1)}%</p>
                              </div>
                              <div className="rounded-xl bg-orange-50 dark:bg-orange-900/20 p-4">
                                <p className="text-sm text-gray-700 dark:text-gray-300 mb-1">User Satisfaction</p>
                                <p className="text-3xl font-bold text-orangePrimary">{(metricsData.user_satisfaction * 100).toFixed(1)}%</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    <Button
                      variant="outline"
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
                      className="bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-200"
                    >
                      <BarChart3 className="mr-2 h-4 w-4" />
                      {isSelected ? "Hide" : "Metrics"}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        if (confirm(`Delete agent "${agent.name}"?`)) {
                          deleteMutation.mutate(agent.agent_id)
                        }
                      }}
                      disabled={deleteMutation.isPending}
                      className="bg-red-50 hover:bg-red-100 text-red-700 border-red-200"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </Button>
                  </div>
                </div>
              </ModernCard>
            )
          })}
        </div>
      )}
    </div>
  )
}
