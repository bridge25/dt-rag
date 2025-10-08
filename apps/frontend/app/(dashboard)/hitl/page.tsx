"use client"

import { useState, useEffect } from "react"
import { getHITLTasks, submitHITLReview, type HITLTask } from "@/lib/api"
import { ModernCard } from "@/components/ui/modern-card"
import { IconBadge } from "@/components/ui/icon-badge"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { ClipboardCheck, RefreshCw, AlertCircle, CheckCircle2, AlertTriangle, Clock } from "lucide-react"

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
    <div className="space-y-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-6">
      <ModernCard variant="purple">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <IconBadge icon={ClipboardCheck} color="orange" size="lg" />
            <div>
              <h1 className="text-3xl font-bold">HITL Review Queue</h1>
              <p className="mt-1 text-sm text-white/80">
                Human-in-the-loop classification review for low-confidence predictions
              </p>
            </div>
          </div>
          <Button
            onClick={loadTasks}
            disabled={loading}
            className="bg-white/20 hover:bg-white/30 text-white border-white/30"
            size="lg"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            {loading ? "Loading..." : "Refresh"}
          </Button>
        </div>
      </ModernCard>

      {loading ? (
        <ModernCard variant="beige">
          <div className="flex flex-col items-center justify-center py-12">
            <RefreshCw className="h-12 w-12 text-orangePrimary animate-spin mb-4" />
            <p className="text-lg font-medium text-gray-700">Loading tasks...</p>
          </div>
        </ModernCard>
      ) : tasks.length === 0 ? (
        <ModernCard variant="green">
          <div className="text-center py-12">
            <IconBadge icon={CheckCircle2} color="teal" size="lg" className="mx-auto mb-4" />
            <h2 className="text-3xl font-bold mb-2">All Clear!</h2>
            <p className="text-lg text-white/80">No pending HITL tasks require review</p>
          </div>
        </ModernCard>
      ) : (
        <div className="grid gap-4">
          {tasks.map((task) => {
            const priorityInfo = getPriorityIcon(task.priority)
            const isSelected = selectedTask?.task_id === task.task_id

            return (
              <ModernCard
                key={task.task_id}
                variant={isSelected ? "teal" : "default"}
                className={`cursor-pointer transition-all duration-300 ${
                  isSelected ? "ring-4 ring-tealAccent/30 scale-[1.01]" : "hover:shadow-card"
                }`}
                onClick={() => {
                  setSelectedTask(task)
                  setSelectedPath(task.suggested_classification)
                  setReviewerNotes("")
                }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <IconBadge icon={priorityInfo.icon} color={priorityInfo.color} size="sm" />
                    <div className="flex flex-col">
                      <span className={`text-xs font-bold uppercase ${isSelected ? "text-gray-900" : "text-muted-foreground"}`}>
                        {task.priority}
                      </span>
                      <span className={`text-xs ${isSelected ? "text-gray-700" : "text-muted-foreground"}`}>
                        {new Date(task.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <div className={`rounded-full px-3 py-1 ${isSelected ? "bg-gray-900/10" : "bg-orangePrimary/20"}`}>
                    <span className={`text-sm font-bold ${isSelected ? "text-gray-900" : "text-orangePrimary"}`}>
                      {(task.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                <p className={`mb-4 leading-relaxed text-base ${isSelected ? "text-gray-900" : "text-gray-800 dark:text-gray-200"}`}>
                  {task.text}
                </p>

                <div className={`rounded-xl p-4 ${isSelected ? "bg-white/50" : "bg-gray-100 dark:bg-gray-800"}`}>
                  <p className={`text-xs font-semibold mb-2 ${isSelected ? "text-gray-900" : "text-gray-600 dark:text-gray-400"}`}>
                    Suggested Classification:
                  </p>
                  <div className="flex items-center flex-wrap gap-2">
                    {task.suggested_classification.map((part, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        {idx > 0 && <span className={isSelected ? "text-gray-700" : "text-gray-400"}>→</span>}
                        <span className={`inline-block px-3 py-1 rounded-lg text-sm font-medium ${
                          isSelected
                            ? "bg-purpleFolder/20 text-purpleFolder"
                            : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                        }`}>
                          {part}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {selectedTask?.task_id === task.task_id && (
                  <div className="mt-6 pt-6 border-t border-gray-900/20">
                    <div className="space-y-4">
                      <div>
                        <Label className="text-gray-900 text-sm font-semibold mb-3 block">
                          Select Classification Path:
                        </Label>
                        <div className="space-y-2">
                          <Button
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedPath(task.suggested_classification)
                            }}
                            variant={
                              JSON.stringify(selectedPath) === JSON.stringify(task.suggested_classification)
                                ? "default"
                                : "outline"
                            }
                            className={`w-full justify-start text-left h-auto py-3 ${
                              JSON.stringify(selectedPath) === JSON.stringify(task.suggested_classification)
                                ? "bg-purpleFolder text-white hover:bg-purpleFolder/90"
                                : "bg-white/50 text-gray-900 hover:bg-white/80"
                            }`}
                          >
                            {task.suggested_classification.join(" → ")}
                          </Button>
                        </div>
                      </div>

                      <div>
                        <Label className="text-gray-900 text-sm font-semibold mb-2 block">
                          Reviewer Notes (optional):
                        </Label>
                        <Textarea
                          value={reviewerNotes}
                          onChange={(e) => setReviewerNotes(e.target.value)}
                          onClick={(e) => e.stopPropagation()}
                          className="bg-white/50 border-gray-900/20 text-gray-900 placeholder:text-gray-600"
                          rows={3}
                          placeholder="Add notes about your classification decision..."
                        />
                      </div>

                      <div className="flex justify-end gap-3">
                        <Button
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedTask(null)
                            setSelectedPath([])
                            setReviewerNotes("")
                          }}
                          disabled={submitting}
                          variant="outline"
                          className="bg-white/50 text-gray-900 hover:bg-white/80 border-gray-900/20"
                        >
                          Cancel
                        </Button>
                        <Button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleSubmitReview()
                          }}
                          disabled={submitting || selectedPath.length === 0}
                          className="bg-purpleFolder hover:bg-purpleFolder/90 text-white"
                        >
                          {submitting ? "Submitting..." : "Submit Review"}
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </ModernCard>
            )
          })}
        </div>
      )}
    </div>
  )
}
