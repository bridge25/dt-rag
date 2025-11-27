/**
 * Pipeline page - System Flow
 *
 * @CODE:FRONTEND-MIGRATION-005
 */

"use client"

import { useState, useEffect } from "react"
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
  Activity,
  Terminal,
  Cpu,
  Zap,
  GitCommit
} from "lucide-react"
import { cn } from "@/lib/utils"

type PipelineStep = {
  id: string
  name: string
  description: string
  icon: typeof Network
  color: "red" | "orange" | "blue" | "green" | "purple" | "teal"
  status: "completed" | "running" | "pending" | "error"
  duration?: number
  details?: string
  logs?: string[]
}

export default function PipelinePage() {
  const [selectedStep, setSelectedStep] = useState<string | null>(null)
  const [activePulse, setActivePulse] = useState(0)

  // Simulate pulsing effect
  useEffect(() => {
    const interval = setInterval(() => {
      setActivePulse(prev => (prev + 1) % 3)
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  const pipelineSteps: PipelineStep[] = [
    {
      id: "query-analysis",
      name: "Query Analysis",
      description: "Analyze and preprocess user query",
      icon: Search,
      color: "blue",
      status: "completed",
      duration: 12,
      details: "Tokenization, intent detection, entity extraction",
      logs: [
        "[INFO] Received query: 'What is machine learning?'",
        "[INFO] Detected intent: DEFINITION",
        "[INFO] Extracted entities: ['machine learning']"
      ]
    },
    {
      id: "classification",
      name: "Classification",
      description: "Taxonomy-based classification",
      icon: Network,
      color: "purple",
      status: "completed",
      duration: 25,
      details: "LLM-based classification with confidence scoring",
      logs: [
        "[INFO] Classifying against 150 taxonomy nodes",
        "[SUCCESS] Matched: /technology/ai/ml (0.98)"
      ]
    },
    {
      id: "retrieval",
      name: "Hybrid Retrieval",
      description: "BM25 + Vector similarity search",
      icon: Filter,
      color: "green",
      status: "completed",
      duration: 45,
      details: "Parallel BM25 and vector search, merge results",
      logs: [
        "[INFO] Vector Search: 15 results found",
        "[INFO] BM25 Search: 12 results found",
        "[INFO] Merged: 20 unique chunks"
      ]
    },
    {
      id: "reranking",
      name: "Reranking",
      description: "Cross-encoder reranking",
      icon: TrendingUp,
      color: "orange",
      status: "completed",
      duration: 38,
      details: "Cross-encoder model for accurate relevance scoring",
      logs: [
        "[INFO] Reranking top 20 chunks",
        "[INFO] Top score: 0.92, Lowest score: 0.45"
      ]
    },
    {
      id: "context-building",
      name: "Context Building",
      description: "Build context from top results",
      icon: FileText,
      color: "teal",
      status: "completed",
      duration: 15,
      details: "Context assembly, deduplication, formatting",
      logs: [
        "[INFO] Assembling context window (4096 tokens)",
        "[INFO] Added 5 chunks to context"
      ]
    },
    {
      id: "llm-generation",
      name: "LLM Generation",
      description: "Generate answer using LLM",
      icon: Sparkles,
      color: "purple",
      status: "running",
      duration: 420,
      details: "Gemini-based answer generation with streaming",
      logs: [
        "[INFO] Sending prompt to Gemini Pro",
        "[INFO] Streaming response..."
      ]
    },
    {
      id: "source-attribution",
      name: "Source Attribution",
      description: "Add citations and sources",
      icon: Link2,
      color: "blue",
      status: "pending",
      duration: 0,
      details: "Extract and attach source metadata",
      logs: []
    }
  ]

  const getTotalDuration = () => {
    return pipelineSteps.reduce((sum, step) => sum + (step.duration || 0), 0)
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-dark-navy relative overflow-hidden p-8">
      {/* Ambient Background */}
      <div className="absolute bottom-0 left-0 w-[1000px] h-[600px] bg-accent-glow-green/5 blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-white/5 border border-white/10 backdrop-blur-md">
                <Activity className="w-6 h-6 text-accent-glow-green" />
              </div>
              <h1 className="text-4xl font-bold tracking-tight text-white">System Flow</h1>
            </div>
            <p className="text-gray-400 max-w-xl">
              Real-time visualization of the RAG inference pipeline.
            </p>
          </div>

          <div className="flex gap-4">
            <div className="px-6 py-3 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md flex flex-col items-end">
              <span className="text-xs font-mono text-gray-400 uppercase tracking-wider">Total Latency</span>
              <span className="text-2xl font-bold text-white font-mono">{getTotalDuration()}ms</span>
            </div>
            <div className="px-6 py-3 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md flex flex-col items-end">
              <span className="text-xs font-mono text-gray-400 uppercase tracking-wider">Status</span>
              <div className="flex items-center gap-2 mt-1">
                <div className="w-2 h-2 rounded-full bg-accent-glow-green animate-pulse" />
                <span className="text-lg font-bold text-accent-glow-green">ACTIVE</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Pipeline Steps Column */}
          <div className="lg:col-span-2 space-y-6">
            <div className="relative">
              {/* Connecting Line */}
              <div className="absolute left-8 top-8 bottom-8 w-0.5 bg-gradient-to-b from-accent-glow-blue/20 via-accent-glow-purple/20 to-accent-glow-green/20" />

              <div className="space-y-6">
                {pipelineSteps.map((step, index) => {
                  const isSelected = selectedStep === step.id
                  const isRunning = step.status === "running"

                  return (
                    <div
                      key={step.id}
                      className={cn(
                        "relative pl-20 transition-all duration-500",
                        isSelected ? "scale-[1.02]" : "opacity-80 hover:opacity-100"
                      )}
                      onClick={() => setSelectedStep(isSelected ? null : step.id)}
                    >
                      {/* Node Connector */}
                      <div className={cn(
                        "absolute left-6 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 transition-all duration-300 z-10",
                        step.status === "completed" ? "bg-dark-navy border-accent-glow-green shadow-[0_0_10px_rgba(74,222,128,0.5)]" :
                          step.status === "running" ? "bg-dark-navy border-accent-glow-blue shadow-[0_0_15px_rgba(96,165,250,0.8)] animate-pulse" :
                            "bg-dark-navy border-gray-600"
                      )} />

                      {/* Horizontal Line */}
                      <div className={cn(
                        "absolute left-10 top-1/2 -translate-y-1/2 h-0.5 w-10 transition-colors duration-300",
                        isSelected ? "bg-accent-glow-blue" : "bg-white/10"
                      )} />

                      <div className={cn(
                        "group relative overflow-hidden rounded-2xl border backdrop-blur-md transition-all duration-300 cursor-pointer",
                        isSelected
                          ? "bg-white/10 border-accent-glow-blue/50 shadow-glass"
                          : "bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/10"
                      )}>
                        {/* Progress Bar Background */}
                        {isRunning && (
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-accent-glow-blue/5 to-transparent -skew-x-12 animate-shimmer" />
                        )}

                        <div className="p-5 flex items-start gap-5 relative z-10">
                          <div className={cn(
                            "p-3 rounded-xl border transition-colors duration-300",
                            isSelected ? "bg-accent-glow-blue/20 border-accent-glow-blue/30" : "bg-white/5 border-white/10"
                          )}>
                            <step.icon className={cn(
                              "w-6 h-6",
                              isSelected ? "text-accent-glow-blue" : "text-gray-400"
                            )} />
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between mb-1">
                              <h3 className={cn(
                                "text-lg font-bold transition-colors",
                                isSelected ? "text-white" : "text-gray-300"
                              )}>
                                {step.name}
                              </h3>
                              <div className="flex items-center gap-3">
                                {step.duration && (
                                  <span className="text-xs font-mono text-gray-500 bg-black/20 px-2 py-1 rounded">
                                    {step.duration}ms
                                  </span>
                                )}
                                {step.status === "completed" && <CheckCircle2 className="w-5 h-5 text-accent-glow-green" />}
                                {step.status === "running" && <Cpu className="w-5 h-5 text-accent-glow-blue animate-spin" />}
                              </div>
                            </div>

                            <p className="text-sm text-gray-400 mb-3">
                              {step.description}
                            </p>

                            {/* Mini Visualization */}
                            <div className="flex gap-1 h-1.5 w-full max-w-[200px] rounded-full overflow-hidden bg-black/20">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={cn(
                                    "flex-1 transition-all duration-300",
                                    step.status === "completed" ? "bg-accent-glow-green/50" :
                                      step.status === "running" && i <= activePulse ? "bg-accent-glow-blue" :
                                        "bg-white/5"
                                  )}
                                />
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Details & Logs Column */}
          <div className="lg:col-span-1 space-y-6">
            <div className="sticky top-8">
              <div className="rounded-3xl bg-black/40 border border-white/10 backdrop-blur-xl overflow-hidden shadow-2xl">
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-white/5">
                  <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-gray-400" />
                    <span className="text-sm font-mono text-gray-300">SYSTEM_LOGS</span>
                  </div>
                  <div className="flex gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/50" />
                    <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 border border-green-500/50" />
                  </div>
                </div>

                <div className="p-6 min-h-[400px] font-mono text-xs space-y-4">
                  {selectedStep ? (
                    <div className="animate-in fade-in duration-300">
                      <div className="mb-4 pb-4 border-b border-white/5">
                        <span className="text-accent-glow-blue"># Viewing logs for: </span>
                        <span className="text-white font-bold">{pipelineSteps.find(s => s.id === selectedStep)?.name}</span>
                      </div>
                      {pipelineSteps.find(s => s.id === selectedStep)?.logs?.map((log, i) => (
                        <div key={i} className="text-gray-300 mb-2 break-all">
                          <span className="text-gray-600 mr-2">{new Date().toLocaleTimeString()}</span>
                          {log}
                        </div>
                      )) || <span className="text-gray-500 italic">// No logs available for this step</span>}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-[300px] text-gray-500 gap-4">
                      <GitCommit className="w-12 h-12 opacity-20" />
                      <p>Select a pipeline step to inspect logs</p>
                    </div>
                  )}

                  {/* Blinking Cursor */}
                  <div className="w-2 h-4 bg-accent-glow-green animate-pulse mt-4" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
