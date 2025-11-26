/**
 * HITL page - Decision Interface
 *
 * @CODE:FRONTEND-MIGRATION-006
 */

"use client"

import { useState, useEffect } from "react"
import { getHITLTasks, submitHITLReview, type HITLTask } from "@/lib/api"
import { IconBadge } from "@/components/ui/icon-badge"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { ClipboardCheck, RefreshCw, AlertCircle, CheckCircle2, AlertTriangle, Clock, GitPullRequest, ArrowRight, Check, X } from "lucide-react"
import { cn } from "@/lib/utils"

export default function HITLPage() {
  const [tasks, setTasks] = useState<HITLTask[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTask, setSelectedTask] = useState<HITLTask | null>(null)
  const [reviewerNotes, setReviewerNotes] = useState("")
  const [selectedPath, setSelectedPath] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadTasks()
  }, [])

  const loadTasks = async () => {
    setLoading(true)
    try {
      const data = await getHITLTasks({ limit: 20 })
      setTasks(data)
    } catch (error) {
      console.error("Failed to load HITL tasks:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitReview = async () => {
    if (!selectedTask || selectedPath.length === 0) {
      alert("Please select a classification path")
      return
    }

    setSubmitting(true)
    try {
      await submitHITLReview({
        chunk_id: selectedTask.chunk_id,
        approved_path: selectedPath,
        reviewer_notes: reviewerNotes || undefined,
      })

      setSelectedTask(null)
      setSelectedPath([])
      setReviewerNotes("")
      await loadTasks()
    } catch (error) {
      console.error("Failed to submit review:", error)
      alert("Failed to submit review")
    } finally {
      setSubmitting(false)
    }
  }

  const getPriorityIcon = (priority: string): { icon: typeof AlertCircle; color: "red" | "orange" | "blue" | "green" | "purple" | "teal" } => {
    switch (priority) {
      case "urgent":
        return { icon: AlertCircle, color: "red" }
      case "high":
        return { icon: AlertTriangle, color: "orange" }
      case "normal":
        return { icon: Clock, color: "blue" }
      case "low":
        return { icon: CheckCircle2, color: "green" }
      default:
        return { icon: Clock, color: "blue" }
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-dark-navy relative overflow-hidden p-8">
      {/* Ambient Background */}
      <div className="absolute top-0 left-0 w-[800px] h-[800px] bg-accent-glow-orange/5 blur-[100px] rounded-full pointer-events-none" />

      <div className="max-w-6xl mx-auto space-y-8 relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-white/5 border border-white/10 backdrop-blur-md">
                <ClipboardCheck className="w-6 h-6 text-accent-glow-orange" />
              </div>
              <h1 className="text-4xl font-bold tracking-tight text-white">Decision Interface</h1>
            </div>
            <p className="text-gray-400 max-w-xl">
              Human-in-the-Loop review queue for low-confidence classifications.
            </p>
          </div>

          <Button
            onClick={loadTasks}
            disabled={loading}
            className="bg-white/5 hover:bg-white/10 text-white border border-white/10 backdrop-blur-md"
            size="lg"
          >
            <RefreshCw className={cn("mr-2 h-4 w-4", loading && "animate-spin")} />
            {loading ? "SYNCING..." : "SYNC QUEUE"}
          </Button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-24 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-md">
            <div className="relative">
              <div className="absolute inset-0 bg-accent-glow-orange/20 blur-xl rounded-full" />
              <RefreshCw className="relative h-12 w-12 text-accent-glow-orange animate-spin" />
            </div>
            <p className="mt-6 text-lg font-medium text-white">Retrieving tasks...</p>
          </div>
        ) : tasks.length === 0 ? (
          <div className="text-center py-24 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-md">
            <div className="inline-flex p-6 rounded-full bg-accent-glow-green/10 border border-accent-glow-green/20 mb-6">
              <CheckCircle2 className="h-12 w-12 text-accent-glow-green" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-2">Queue Cleared</h2>
            <p className="text-lg text-gray-400">All classification tasks have been processed.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Task List */}
            <div className="lg:col-span-1 space-y-4">
              <div className="flex items-center justify-between px-2">
                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Pending Reviews</h3>
                <span className="px-2 py-0.5 rounded-full bg-accent-glow-orange/10 text-xs font-mono text-accent-glow-orange border border-accent-glow-orange/20">
                  {tasks.length} TASKS
                </span>
              </div>

              <div className="space-y-3">
                {tasks.map((task) => {
                  const priorityInfo = getPriorityIcon(task.priority)
                  const isSelected = selectedTask?.task_id === task.task_id

                  return (
                    <div
                      key={task.task_id}
                      className={cn(
                        "group relative p-4 rounded-xl border transition-all duration-300 cursor-pointer hover:-translate-y-0.5",
                        isSelected
                          ? "bg-accent-glow-orange/10 border-accent-glow-orange/50 shadow-[0_0_20px_rgba(249,115,22,0.1)]"
                          : "bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/10"
                      )}
                      onClick={() => {
                        setSelectedTask(task)
                        setSelectedPath(task.suggested_classification)
                        setReviewerNotes("")
                      }}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <priorityInfo.icon className={cn("w-4 h-4", `text-${priorityInfo.color}-400`)} />
                          <span className={cn(
                            "text-xs font-bold uppercase tracking-wider",
                            `text-${priorityInfo.color}-400`
                          )}>
                            {task.priority}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-gray-500">
                          {new Date(task.created_at).toLocaleTimeString()}
                        </span>
                      </div>

                      <p className="text-sm text-gray-300 line-clamp-2 mb-3">
                        {task.text}
                      </p>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] text-gray-500 uppercase">Confidence</span>
                          <div className="h-1 w-16 bg-white/10 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-accent-glow-orange"
                              style={{ width: `${task.confidence * 100}%` }}
                            />
                          </div>
                        </div>
                        <span className="text-xs font-mono text-accent-glow-orange">
                          {(task.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Review Panel */}
            <div className="lg:col-span-2">
              {selectedTask ? (
                <div className="sticky top-8 rounded-3xl bg-glass border border-white/10 backdrop-blur-xl overflow-hidden shadow-2xl animate-in fade-in slide-in-from-right-4 duration-500">
                  {/* Review Header */}
                  <div className="px-8 py-6 border-b border-white/5 bg-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-accent-glow-orange/10 border border-accent-glow-orange/20">
                        <GitPullRequest className="w-5 h-5 text-accent-glow-orange" />
                      </div>
                      <div>
                        <h2 className="text-lg font-bold text-white">Review Task</h2>
                        <p className="text-xs text-gray-400 font-mono">ID: {selectedTask.task_id}</p>
                      </div>
                    </div>
                    <div className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-gray-300">
                      WAITING_FOR_APPROVAL
                    </div>
                  </div>

                  <div className="p-8 space-y-8">
                    {/* Content Preview */}
                    <div className="space-y-3">
                      <Label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Source Content</Label>
                      <div className="p-6 rounded-2xl bg-black/30 border border-white/5 text-gray-200 leading-relaxed text-lg font-light">
                        {selectedTask.text}
                      </div>
                    </div>

                    {/* Classification Path */}
                    <div className="space-y-3">
                      <Label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Classification Path</Label>
                      <div className="p-1 rounded-xl bg-white/5 border border-white/5">
                        <div className="flex items-center gap-2 p-2 overflow-x-auto">
                          {selectedTask.suggested_classification.map((part, idx) => (
                            <div key={idx} className="flex items-center gap-2 flex-shrink-0">
                              {idx > 0 && <ArrowRight className="w-4 h-4 text-gray-600" />}
                              <span className={cn(
                                "px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors",
                                "bg-accent-glow-blue/10 text-accent-glow-blue border-accent-glow-blue/20"
                              )}>
                                {part}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Reviewer Actions */}
                    <div className="space-y-4 pt-4 border-t border-white/5">
                      <div className="space-y-3">
                        <Label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Reviewer Notes</Label>
                        <Textarea
                          value={reviewerNotes}
                          onChange={(e) => setReviewerNotes(e.target.value)}
                          className="bg-white/5 border-white/10 text-white placeholder:text-gray-600 min-h-[100px] focus:border-accent-glow-orange/50"
                          placeholder="Add context for your decision..."
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4 pt-4">
                        <Button
                          onClick={() => {
                            setSelectedTask(null)
                            setSelectedPath([])
                            setReviewerNotes("")
                          }}
                          disabled={submitting}
                          variant="outline"
                          className="h-14 border-white/10 text-gray-300 hover:bg-white/5 hover:text-white"
                        >
                          <X className="w-5 h-5 mr-2" />
                          Skip Task
                        </Button>
                        <Button
                          onClick={handleSubmitReview}
                          disabled={submitting || selectedPath.length === 0}
                          className="h-14 bg-accent-glow-orange hover:bg-accent-glow-orange/90 text-white shadow-lg shadow-accent-glow-orange/20"
                        >
                          {submitting ? (
                            <RefreshCw className="w-5 h-5 animate-spin mr-2" />
                          ) : (
                            <Check className="w-5 h-5 mr-2" />
                          )}
                          {submitting ? "Processing..." : "Approve Classification"}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4 min-h-[400px] rounded-3xl border-2 border-dashed border-white/5">
                  <div className="p-4 rounded-full bg-white/5">
                    <GitPullRequest className="w-8 h-8 opacity-50" />
                  </div>
                  <p>Select a task from the queue to begin review</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
