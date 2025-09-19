'use client'

import React, { useState, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CheckCircle,
  XCircle,
  Edit3,
  Users,
  Clock,
  TrendingUp,
  Filter,
  Search,
  Download,
  MoreHorizontal,
  AlertTriangle,
  User,
  Calendar
} from 'lucide-react'
import { ClassificationQueueItem, BatchOperation } from '@/types/taxonomy'
import { cn } from '@/lib/utils'

interface HITLQueueProps {
  queueItems: ClassificationQueueItem[]
  onApprove: (itemId: string, correction?: string) => void
  onReject: (itemId: string, reason: string) => void
  onBatchOperation: (operation: BatchOperation) => void
  className?: string
}

interface HITLFilters {
  status: ClassificationQueueItem['status'][]
  confidenceRange: [number, number]
  dateRange: [string, string] | null
  searchQuery: string
}

export function HITLQueue({
  queueItems,
  onApprove,
  onReject,
  onBatchOperation,
  className
}: HITLQueueProps) {
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())
  const [filters, setFilters] = useState<HITLFilters>({
    status: ['pending'],
    confidenceRange: [0, 1],
    dateRange: null,
    searchQuery: ''
  })
  const [showFilters, setShowFilters] = useState(false)
  const [editingItem, setEditingItem] = useState<string | null>(null)
  const [editText, setEditText] = useState('')

  // Filter and sort items
  const filteredItems = useMemo(() => {
    return queueItems
      .filter(item => {
        // Status filter
        if (!filters.status.includes(item.status)) return false

        // Confidence filter
        if (item.confidence < filters.confidenceRange[0] ||
            item.confidence > filters.confidenceRange[1]) return false

        // Date filter
        if (filters.dateRange) {
          const itemDate = new Date(item.created_at)
          const startDate = new Date(filters.dateRange[0])
          const endDate = new Date(filters.dateRange[1])
          if (itemDate < startDate || itemDate > endDate) return false
        }

        // Search filter
        if (filters.searchQuery) {
          const query = filters.searchQuery.toLowerCase()
          return (
            item.text.toLowerCase().includes(query) ||
            item.suggested_path.some(path => path.toLowerCase().includes(query))
          )
        }

        return true
      })
      .sort((a, b) => {
        // Sort by status (pending first), then by confidence (low first), then by date
        if (a.status !== b.status) {
          const statusOrder = { pending: 0, approved: 1, rejected: 2, modified: 3 }
          return statusOrder[a.status] - statusOrder[b.status]
        }
        if (a.status === 'pending') {
          return a.confidence - b.confidence // Low confidence first for review
        }
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      })
  }, [queueItems, filters])

  const toggleItemSelection = useCallback((itemId: string, selected: boolean) => {
    setSelectedItems(prev => {
      const newSet = new Set(prev)
      if (selected) {
        newSet.add(itemId)
      } else {
        newSet.delete(itemId)
      }
      return newSet
    })
  }, [])

  const toggleAllSelection = useCallback(() => {
    const pendingItems = filteredItems.filter(item => item.status === 'pending')
    const allSelected = pendingItems.every(item => selectedItems.has(item.id))

    setSelectedItems(
      allSelected
        ? new Set()
        : new Set(pendingItems.map(item => item.id))
    )
  }, [filteredItems, selectedItems])

  const handleBatchApprove = useCallback(() => {
    if (selectedItems.size === 0) return

    onBatchOperation({
      type: 'approve_all',
      items: Array.from(selectedItems),
      reviewer: 'current_user', // TODO: Get from auth context
      notes: 'Batch approval'
    })

    setSelectedItems(new Set())
  }, [selectedItems, onBatchOperation])

  const handleBatchReject = useCallback(() => {
    if (selectedItems.size === 0) return

    onBatchOperation({
      type: 'reject_all',
      items: Array.from(selectedItems),
      reviewer: 'current_user',
      notes: 'Batch rejection'
    })

    setSelectedItems(new Set())
  }, [selectedItems, onBatchOperation])

  const handleApproveHighConfidence = useCallback(() => {
    const highConfidenceItems = filteredItems
      .filter(item => item.status === 'pending' && item.confidence >= 0.8)
      .map(item => item.id)

    if (highConfidenceItems.length === 0) return

    onBatchOperation({
      type: 'approve_high_confidence',
      items: highConfidenceItems,
      reviewer: 'current_user',
      notes: 'Auto-approval for high confidence items'
    })
  }, [filteredItems, onBatchOperation])

  const handleEdit = useCallback((item: ClassificationQueueItem) => {
    setEditingItem(item.id)
    setEditText(item.suggested_path.join(' > '))
  }, [])

  const handleSaveEdit = useCallback((itemId: string) => {
    const newPath = editText.split(' > ').map(s => s.trim()).filter(Boolean)
    onApprove(itemId, newPath.join(' > '))
    setEditingItem(null)
    setEditText('')
  }, [editText, onApprove])

  const getStatusColor = (status: ClassificationQueueItem['status']) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600 bg-yellow-50'
      case 'approved':
        return 'text-green-600 bg-green-50'
      case 'rejected':
        return 'text-red-600 bg-red-50'
      case 'modified':
        return 'text-blue-600 bg-blue-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const pendingCount = filteredItems.filter(item => item.status === 'pending').length
  const highConfidenceCount = filteredItems.filter(
    item => item.status === 'pending' && item.confidence >= 0.8
  ).length

  return (
    <div className={cn("flex flex-col space-y-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold">Human Review Queue</h1>
          <div className="flex items-center space-x-2">
            <span className={cn(
              "px-2 py-1 rounded text-sm font-medium",
              pendingCount > 0 ? "text-yellow-600 bg-yellow-50" : "text-green-600 bg-green-50"
            )}>
              {pendingCount} pending
            </span>
            {highConfidenceCount > 0 && (
              <span className="px-2 py-1 rounded text-sm font-medium text-green-600 bg-green-50">
                {highConfidenceCount} high confidence
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              "flex items-center space-x-2 px-3 py-2 rounded-md border",
              "hover:bg-accent transition-colors",
              showFilters && "bg-accent"
            )}
          >
            <Filter className="h-4 w-4" />
            <span className="text-sm">Filters</span>
          </button>

          <button
            onClick={handleApproveHighConfidence}
            disabled={highConfidenceCount === 0}
            className={cn(
              "flex items-center space-x-2 px-3 py-2 rounded-md",
              "bg-green-600 text-white hover:bg-green-700",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            <TrendingUp className="h-4 w-4" />
            <span className="text-sm">Auto-approve High Confidence</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border rounded-lg p-4 bg-accent/50"
          >
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search */}
              <div>
                <label className="block text-sm font-medium mb-1">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Search text or path..."
                    value={filters.searchQuery}
                    onChange={(e) => setFilters(prev => ({ ...prev, searchQuery: e.target.value }))}
                    className="w-full pl-10 pr-3 py-2 border rounded-md text-sm"
                  />
                </div>
              </div>

              {/* Status */}
              <div>
                <label className="block text-sm font-medium mb-1">Status</label>
                <select
                  multiple
                  value={filters.status}
                  onChange={(e) => {
                    const values = Array.from(e.target.selectedOptions, option => option.value as ClassificationQueueItem['status'])
                    setFilters(prev => ({ ...prev, status: values }))
                  }}
                  className="w-full border rounded-md text-sm p-2"
                >
                  <option value="pending">Pending</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                  <option value="modified">Modified</option>
                </select>
              </div>

              {/* Confidence Range */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  Confidence: {(filters.confidenceRange[0] * 100).toFixed(0)}% - {(filters.confidenceRange[1] * 100).toFixed(0)}%
                </label>
                <div className="space-y-2">
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={filters.confidenceRange[0]}
                    onChange={(e) => setFilters(prev => ({
                      ...prev,
                      confidenceRange: [parseFloat(e.target.value), prev.confidenceRange[1]]
                    }))}
                    className="w-full"
                  />
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={filters.confidenceRange[1]}
                    onChange={(e) => setFilters(prev => ({
                      ...prev,
                      confidenceRange: [prev.confidenceRange[0], parseFloat(e.target.value)]
                    }))}
                    className="w-full"
                  />
                </div>
              </div>

              {/* Clear Filters */}
              <div className="flex items-end">
                <button
                  onClick={() => setFilters({
                    status: ['pending'],
                    confidenceRange: [0, 1],
                    dateRange: null,
                    searchQuery: ''
                  })}
                  className="px-3 py-2 border rounded-md text-sm hover:bg-accent"
                >
                  Clear Filters
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Batch Actions */}
      {selectedItems.size > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between p-3 bg-primary/10 border border-primary/20 rounded-lg"
        >
          <span className="text-sm font-medium">
            {selectedItems.size} item{selectedItems.size !== 1 ? 's' : ''} selected
          </span>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleBatchApprove}
              className="flex items-center space-x-1 px-3 py-1 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm"
            >
              <CheckCircle className="h-4 w-4" />
              <span>Approve All</span>
            </button>
            <button
              onClick={handleBatchReject}
              className="flex items-center space-x-1 px-3 py-1 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
            >
              <XCircle className="h-4 w-4" />
              <span>Reject All</span>
            </button>
          </div>
        </motion.div>
      )}

      {/* Queue Items */}
      <div className="space-y-3">
        {/* Select All */}
        {pendingCount > 0 && (
          <div className="flex items-center space-x-2 p-3 bg-accent/30 rounded-lg">
            <input
              type="checkbox"
              checked={filteredItems.filter(item => item.status === 'pending').every(item => selectedItems.has(item.id))}
              onChange={toggleAllSelection}
              className="rounded"
            />
            <span className="text-sm font-medium">Select all pending items</span>
          </div>
        )}

        {filteredItems.map((item) => (
          <HITLQueueItem
            key={item.id}
            item={item}
            isSelected={selectedItems.has(item.id)}
            isEditing={editingItem === item.id}
            editText={editText}
            onSelect={(selected) => toggleItemSelection(item.id, selected)}
            onApprove={(correction) => onApprove(item.id, correction)}
            onReject={(reason) => onReject(item.id, reason)}
            onEdit={() => handleEdit(item)}
            onSaveEdit={() => handleSaveEdit(item.id)}
            onCancelEdit={() => {
              setEditingItem(null)
              setEditText('')
            }}
            onEditTextChange={setEditText}
          />
        ))}
      </div>

      {/* Empty state */}
      {filteredItems.length === 0 && (
        <div className="text-center py-12">
          <Users className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
          <h3 className="text-lg font-medium text-muted-foreground mb-2">No items in queue</h3>
          <p className="text-sm text-muted-foreground">
            All classifications have been reviewed or no items match your filters.
          </p>
        </div>
      )}
    </div>
  )
}

interface HITLQueueItemProps {
  item: ClassificationQueueItem
  isSelected: boolean
  isEditing: boolean
  editText: string
  onSelect: (selected: boolean) => void
  onApprove: (correction?: string) => void
  onReject: (reason: string) => void
  onEdit: () => void
  onSaveEdit: () => void
  onCancelEdit: () => void
  onEditTextChange: (text: string) => void
}

function HITLQueueItem({
  item,
  isSelected,
  isEditing,
  editText,
  onSelect,
  onApprove,
  onReject,
  onEdit,
  onSaveEdit,
  onCancelEdit,
  onEditTextChange
}: HITLQueueItemProps) {
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [rejectReason, setRejectReason] = useState('')

  const handleReject = () => {
    if (rejectReason.trim()) {
      onReject(rejectReason)
      setShowRejectModal(false)
      setRejectReason('')
    }
  }

  const getStatusColor = (status: ClassificationQueueItem['status']) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600 bg-yellow-50'
      case 'approved':
        return 'text-green-600 bg-green-50'
      case 'rejected':
        return 'text-red-600 bg-red-50'
      case 'modified':
        return 'text-blue-600 bg-blue-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={cn(
        "border rounded-lg p-4 bg-background",
        isSelected && "ring-2 ring-primary",
        item.status === 'pending' && "border-yellow-200 bg-yellow-50/50"
      )}
    >
      <div className="flex items-start space-x-3">
        {/* Selection checkbox */}
        {item.status === 'pending' && (
          <input
            type="checkbox"
            checked={isSelected}
            onChange={(e) => onSelect(e.target.checked)}
            className="mt-1 rounded"
          />
        )}

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span className={cn(
                "px-2 py-1 rounded text-xs font-medium capitalize",
                getStatusColor(item.status)
              )}>
                {item.status}
              </span>
              <span className={cn(
                "font-mono text-sm",
                getConfidenceColor(item.confidence)
              )}>
                {(item.confidence * 100).toFixed(1)}%
              </span>
              <span className="text-xs text-muted-foreground">
                <Calendar className="h-3 w-3 inline mr-1" />
                {new Date(item.created_at).toLocaleDateString()}
              </span>
            </div>

            {item.human_reviewer && (
              <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                <User className="h-3 w-3" />
                <span>{item.human_reviewer}</span>
              </div>
            )}
          </div>

          {/* Text */}
          <div className="mb-3">
            <p className="text-sm text-foreground line-clamp-3">
              {item.text}
            </p>
          </div>

          {/* Suggested Path */}
          <div className="mb-3">
            <div className="text-xs text-muted-foreground mb-1">Suggested Classification:</div>
            {isEditing ? (
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={editText}
                  onChange={(e) => onEditTextChange(e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-md text-sm"
                  placeholder="Enter taxonomy path (e.g., AI > Machine Learning > Classification)"
                />
                <button
                  onClick={onSaveEdit}
                  className="px-3 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700"
                >
                  Save
                </button>
                <button
                  onClick={onCancelEdit}
                  className="px-3 py-2 border rounded-md text-sm hover:bg-accent"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium">
                  {item.suggested_path.join(' → ')}
                </span>
                {item.status === 'pending' && (
                  <button
                    onClick={onEdit}
                    className="p-1 hover:bg-accent rounded"
                    title="Edit classification"
                  >
                    <Edit3 className="h-3 w-3" />
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Correction/Reason */}
          {(item.correction || item.reason) && (
            <div className="mb-3 p-2 bg-accent/30 rounded-md">
              <div className="text-xs text-muted-foreground mb-1">
                {item.correction ? 'Correction:' : 'Rejection Reason:'}
              </div>
              <p className="text-sm">{item.correction || item.reason}</p>
            </div>
          )}

          {/* Actions */}
          {item.status === 'pending' && !isEditing && (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => onApprove()}
                className="flex items-center space-x-1 px-3 py-1 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm"
              >
                <CheckCircle className="h-4 w-4" />
                <span>Approve</span>
              </button>
              <button
                onClick={() => setShowRejectModal(true)}
                className="flex items-center space-x-1 px-3 py-1 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
              >
                <XCircle className="h-4 w-4" />
                <span>Reject</span>
              </button>
              <button
                onClick={onEdit}
                className="flex items-center space-x-1 px-3 py-1 border rounded-md hover:bg-accent text-sm"
              >
                <Edit3 className="h-4 w-4" />
                <span>Modify</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Reject Modal */}
      <AnimatePresence>
        {showRejectModal && (
          <>
            <div className="fixed inset-0 bg-black/50 z-50" onClick={() => setShowRejectModal(false)} />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4"
            >
              <div className="bg-background border rounded-lg shadow-xl max-w-md w-full p-6">
                <h3 className="text-lg font-medium mb-4">Reject Classification</h3>
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">Reason for rejection:</label>
                  <textarea
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                    placeholder="Please provide a reason for rejecting this classification..."
                    className="w-full px-3 py-2 border rounded-md text-sm h-24"
                    autoFocus
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <button
                    onClick={() => setShowRejectModal(false)}
                    className="px-4 py-2 border rounded-md text-sm hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleReject}
                    disabled={!rejectReason.trim()}
                    className="px-4 py-2 bg-red-600 text-white rounded-md text-sm hover:bg-red-700 disabled:opacity-50"
                  >
                    Reject
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </motion.div>
  )
}