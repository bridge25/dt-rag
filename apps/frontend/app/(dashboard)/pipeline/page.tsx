"use client"

import { useState } from "react"
import { ModernCard } from "@/components/ui/modern-card"
import { IconBadge } from "@/components/ui/icon-badge"
import {
  Network,
  Search,
  Filter,
  TrendingUp,
  FileText,
  Sparkles,
  Link2,
  CheckCircle2,
  Clock,
  ArrowRight,
  Activity
} from "lucide-react"

type PipelineStep = {
  id: string
  name: string
  description: string
  icon: typeof Network
  color: "red" | "orange" | "blue" | "green" | "purple" | "teal"
  status: "completed" | "running" | "pending" | "error"
  duration?: number
  details?: string
}

export default function PipelinePage() {
  const [selectedStep, setSelectedStep] = useState<string | null>(null)

  const pipelineSteps: PipelineStep[] = [
    {
      id: "query-analysis",
      name: "Query Analysis",
      description: "Analyze and preprocess user query",
      icon: Search,
      color: "blue",
      status: "completed",
      duration: 12,
      details: "Tokenization, intent detection, entity extraction"
    },
    {
      id: "classification",
      name: "Classification",
      description: "Taxonomy-based classification",
      icon: Network,
      color: "purple",
      status: "completed",
      duration: 25,
      details: "LLM-based classification with confidence scoring"
    },
    {
      id: "retrieval",
      name: "Hybrid Retrieval",
      description: "BM25 + Vector similarity search",
      icon: Filter,
      color: "green",
      status: "completed",
      duration: 45,
      details: "Parallel BM25 and vector search, merge results"
    },
    {
      id: "reranking",
      name: "Reranking",
      description: "Cross-encoder reranking",
      icon: TrendingUp,
      color: "orange",
      status: "completed",
      duration: 38,
      details: "Cross-encoder model for accurate relevance scoring"
    },
    {
      id: "context-building",
      name: "Context Building",
      description: "Build context from top results",
      icon: FileText,
      color: "teal",
      status: "completed",
      duration: 15,
      details: "Context assembly, deduplication, formatting"
    },
    {
      id: "llm-generation",
      name: "LLM Generation",
      description: "Generate answer using LLM",
      icon: Sparkles,
      color: "purple",
      status: "completed",
      duration: 420,
      details: "Gemini-based answer generation with streaming"
    },
    {
      id: "source-attribution",
      name: "Source Attribution",
      description: "Add citations and sources",
      icon: Link2,
      color: "blue",
      status: "completed",
      duration: 8,
      details: "Extract and attach source metadata"
    }
  ]

  const recentExecutions = [
    {
      id: "exec-001",
      query: "What is machine learning?",
      timestamp: new Date(Date.now() - 300000).toISOString(),
      totalDuration: 563,
      status: "completed" as const
    },
    {
      id: "exec-002",
      query: "How does vector search work?",
      timestamp: new Date(Date.now() - 600000).toISOString(),
      totalDuration: 512,
      status: "completed" as const
    },
    {
      id: "exec-003",
      query: "Explain RAG architecture",
      timestamp: new Date(Date.now() - 900000).toISOString(),
      totalDuration: 598,
      status: "completed" as const
    }
  ]

  const getTotalDuration = () => {
    return pipelineSteps.reduce((sum, step) => sum + (step.duration || 0), 0)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return CheckCircle2
      case "running":
        return Clock
      default:
        return Activity
    }
  }

  return (
    <div className="space-y-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-6">
      <ModernCard variant="purple">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <IconBadge icon={Activity} color="orange" size="lg" />
            <div>
              <h1 className="text-3xl font-bold">RAG Pipeline</h1>
              <p className="mt-1 text-sm text-white/80">
                7-step retrieval-augmented generation workflow
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-white/80">Total Duration</p>
            <p className="text-3xl font-bold">{getTotalDuration()}ms</p>
          </div>
        </div>
      </ModernCard>

      <div className="grid gap-4 md:grid-cols-3">
        <ModernCard variant="green">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white/80">Total Steps</p>
              <p className="text-4xl font-bold mt-2">{pipelineSteps.length}</p>
            </div>
            <IconBadge icon={Network} color="teal" size="lg" />
          </div>
        </ModernCard>

        <ModernCard variant="teal">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">Completed</p>
              <p className="text-4xl font-bold mt-2 text-gray-900">
                {pipelineSteps.filter(s => s.status === "completed").length}
              </p>
            </div>
            <IconBadge icon={CheckCircle2} color="green" size="lg" />
          </div>
        </ModernCard>

        <ModernCard variant="dark">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white/80">Avg Duration</p>
              <p className="text-4xl font-bold mt-2">
                {Math.round(getTotalDuration() / pipelineSteps.length)}ms
              </p>
            </div>
            <IconBadge icon={Clock} color="orange" size="lg" />
          </div>
        </ModernCard>
      </div>

      <ModernCard variant="beige">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Pipeline Steps</h2>
        <div className="space-y-4">
          {pipelineSteps.map((step, index) => {
            const isSelected = selectedStep === step.id
            const StatusIcon = getStatusIcon(step.status)

            return (
              <div key={step.id} className="relative">
                {index < pipelineSteps.length - 1 && (
                  <div className="absolute left-6 top-16 w-0.5 h-8 bg-gray-300" />
                )}

                <div
                  className={`rounded-xl transition-all duration-300 cursor-pointer ${
                    isSelected
                      ? "bg-white shadow-lg ring-2 ring-orangePrimary scale-[1.02]"
                      : "bg-white/50 hover:bg-white hover:shadow-md"
                  }`}
                  onClick={() => setSelectedStep(isSelected ? null : step.id)}
                >
                  <div className="p-5">
                    <div className="flex items-start gap-4">
                      <IconBadge icon={step.icon} color={step.color} size="md" />

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-sm font-bold text-gray-500">
                            Step {index + 1}
                          </span>
                          <ArrowRight className="h-4 w-4 text-gray-400" />
                          <h3 className="text-lg font-bold text-gray-900">
                            {step.name}
                          </h3>
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-bold ${
                            step.status === "completed"
                              ? "bg-green-100 text-green-800"
                              : step.status === "running"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-gray-100 text-gray-800"
                          }`}>
                            {step.status.toUpperCase()}
                          </span>
                        </div>

                        <p className="text-sm text-gray-600 mb-3">
                          {step.description}
                        </p>

                        <div className="flex items-center gap-6">
                          {step.duration && (
                            <div className="flex items-center gap-2">
                              <Clock className="h-4 w-4 text-orangePrimary" />
                              <span className="text-sm font-semibold text-orangePrimary">
                                {step.duration}ms
                              </span>
                            </div>
                          )}
                          <StatusIcon className={`h-4 w-4 ${
                            step.status === "completed" ? "text-green-600" : "text-gray-400"
                          }`} />
                        </div>

                        {isSelected && step.details && (
                          <div className="mt-4 pt-4 border-t border-gray-200">
                            <p className="text-xs font-semibold text-gray-600 mb-1">Details:</p>
                            <p className="text-sm text-gray-700">{step.details}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </ModernCard>

      <ModernCard variant="dark">
        <h2 className="text-2xl font-bold mb-6">Recent Executions</h2>
        <div className="space-y-3">
          {recentExecutions.map((execution) => (
            <div
              key={execution.id}
              className="rounded-xl bg-white/10 backdrop-blur-sm p-4 hover:bg-white/15 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-base font-semibold text-white truncate">
                    {execution.query}
                  </p>
                  <div className="flex items-center gap-4 mt-2">
                    <span className="text-xs text-white/70">
                      {new Date(execution.timestamp).toLocaleString()}
                    </span>
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3 text-tealAccent" />
                      <span className="text-xs font-medium text-tealAccent">
                        {execution.totalDuration}ms
                      </span>
                    </div>
                  </div>
                </div>
                <IconBadge
                  icon={execution.status === "completed" ? CheckCircle2 : Activity}
                  color={execution.status === "completed" ? "green" : "orange"}
                  size="sm"
                />
              </div>
            </div>
          ))}
        </div>
      </ModernCard>
    </div>
  )
}
