'use client'

import { useState, useEffect } from 'react'
import { API_CONFIG } from '@/constants/api'
import { HITLTask, HITLTaskSchema } from '@/types/schemas'

interface HITLQueueProps {
  className?: string
}

export default function HITLQueue({ className = '' }: HITLQueueProps) {
  const [tasks, setTasks] = useState<HITLTask[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTask, setSelectedTask] = useState<HITLTask | null>(null)
  const [reviewerNotes, setReviewerNotes] = useState('')
  const [selectedPath, setSelectedPath] = useState<string[]>([])

  useEffect(() => {
    const controller = new AbortController()
    loadTasks(controller.signal)

    return () => {
      controller.abort()
    }
  }, [])

  const loadTasks = async (signal?: AbortSignal) => {
    setLoading(true)
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/classify/hitl/tasks?limit=20`, {
        headers: { 'X-API-Key': API_CONFIG.API_KEY },
        signal
      })
      if (signal?.aborted) return
      if (response.ok) {
        const data = await response.json()
        setTasks(data)
      }
    } catch (error: any) {
      if (error.name === 'AbortError') return
      console.error('Failed to load HITL tasks:', error)
    } finally {
      if (!signal?.aborted) {
        setLoading(false)
      }
    }
  }

  const submitReview = async () => {
    if (!selectedTask || selectedPath.length === 0) {
      alert('Please select a classification path')
      return
    }

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/classify/hitl/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_CONFIG.API_KEY
        },
        body: JSON.stringify({
          chunk_id: selectedTask.chunk_id,
          approved_path: selectedPath,
          reviewer_notes: reviewerNotes || null
        })
      })

      if (response.ok) {
        setSelectedTask(null)
        setSelectedPath([])
        setReviewerNotes('')
        await loadTasks()
      }
    } catch (error) {
      console.error('Failed to submit review:', error)
    }
  }

  const getPriorityBadge = (priority: string) => {
    const colors = {
      high: 'bg-red-100 text-red-800',
      normal: 'bg-blue-100 text-blue-800',
      low: 'bg-gray-100 text-gray-800'
    }
    return colors[priority as keyof typeof colors] || colors.normal
  }

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-900">🔍 HITL Review Queue</h3>
          <button
            onClick={() => loadTasks()}
            className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            Refresh
          </button>
        </div>
        <p className="text-sm text-gray-600 mt-1">
          Tasks requiring human review (confidence &lt; 0.70)
        </p>
      </div>

      {loading ? (
        <div className="p-8 text-center text-gray-500">Loading tasks...</div>
      ) : tasks.length === 0 ? (
        <div className="p-8 text-center text-gray-500">
          ✅ No pending HITL tasks
        </div>
      ) : (
        <div className="divide-y divide-gray-200">
          {tasks.map((task) => (
            <div
              key={task.task_id}
              className={`p-4 hover:bg-gray-50 cursor-pointer ${
                selectedTask?.task_id === task.task_id ? 'bg-blue-50' : ''
              }`}
              onClick={() => {
                setSelectedTask(task)
                setSelectedPath(task.suggested_classification)
              }}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded ${getPriorityBadge(task.priority)}`}>
                      {task.priority}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(task.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-800 line-clamp-2">{task.text}</p>
                </div>
              </div>

              <div className="mt-2">
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-600">Suggested:</span>
                  <div className="flex items-center space-x-1">
                    {task.suggested_classification.map((part, idx) => (
                      <span key={idx} className="text-xs bg-gray-100 px-2 py-0.5 rounded">
                        {part}
                      </span>
                    ))}
                  </div>
                  <span className="text-xs text-gray-500">
                    ({(task.confidence * 100).toFixed(1)}%)
                  </span>
                </div>
              </div>

              {selectedTask?.task_id === task.task_id && (
                <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select Classification Path:
                    </label>
                    <div className="space-y-1">
                      {task.alternatives.map((alt) => (
                        <button
                          key={alt.node_id}
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedPath(alt.canonical_path)
                          }}
                          className={`w-full text-left px-3 py-2 rounded text-sm ${
                            JSON.stringify(selectedPath) === JSON.stringify(alt.canonical_path)
                              ? 'bg-blue-100 border-blue-500'
                              : 'bg-gray-50 border-gray-200'
                          } border`}
                        >
                          {alt.canonical_path.join(' → ')}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Reviewer Notes (optional):
                    </label>
                    <textarea
                      value={reviewerNotes}
                      onChange={(e) => setReviewerNotes(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                      rows={2}
                      placeholder="Add notes about this review..."
                    />
                  </div>

                  <div className="flex justify-end space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedTask(null)
                        setSelectedPath([])
                        setReviewerNotes('')
                      }}
                      className="px-3 py-1 text-sm text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        submitReview()
                      }}
                      className="px-3 py-1 text-sm text-white bg-blue-600 rounded hover:bg-blue-700"
                    >
                      Submit Review
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
