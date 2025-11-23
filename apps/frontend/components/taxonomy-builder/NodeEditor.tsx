"use client"

/**
 * NodeEditor - Side panel for editing node properties
 *
 * @CODE:TAXONOMY-BUILDER-001
 */

import { useState, useEffect, memo } from "react"
import { cn } from "@/lib/utils"
import {
  X,
  Trash2,
  Plus,
  FileText,
  Calendar,
  User,
} from "lucide-react"
import type { NodeEditorProps, TaxonomyNode } from "./types"

export const NodeEditor = memo<NodeEditorProps>(function NodeEditor({
  node,
  allNodes,
  onSave,
  onCancel,
  onDelete,
  onAddChild,
  isNew = false,
}) {
  const [name, setName] = useState(node?.name ?? "")
  const [description, setDescription] = useState(node?.description ?? "")
  const [parentId, setParentId] = useState<string | null>(node?.parentId ?? null)
  const [errors, setErrors] = useState<{ name?: string }>({})

  useEffect(() => {
    if (node) {
      setName(node.name)
      setDescription(node.description ?? "")
      setParentId(node.parentId)
    }
  }, [node])

  const handleSave = () => {
    const newErrors: { name?: string } = {}

    if (!name.trim()) {
      newErrors.name = "Name is required"
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    onSave({
      name: name.trim(),
      description: description.trim() || undefined,
      parentId,
    })
  }

  const availableParents = allNodes.filter((n) => {
    if (!node) return true
    // Cannot be its own parent or a descendant
    return n.id !== node.id && !isDescendant(node.id, n.id, allNodes)
  })

  if (!node && !isNew) {
    return (
      <div className="w-80 border-l border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-6 flex items-center justify-center">
        <p className="text-gray-500 dark:text-gray-400 text-center">
          Select a node to view details
        </p>
      </div>
    )
  }

  return (
    <div className="w-80 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {isNew ? "New Node" : "Edit Node"}
        </h3>
        <button
          onClick={onCancel}
          className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded"
          aria-label="Close panel"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Form */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Name */}
        <div>
          <label
            htmlFor="node-name"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Name *
          </label>
          <input
            id="node-name"
            type="text"
            value={name}
            onChange={(e) => {
              setName(e.target.value)
              setErrors({})
            }}
            className={cn(
              "w-full px-3 py-2 border rounded-lg text-sm",
              "focus:outline-none focus:ring-2 focus:ring-blue-500",
              "dark:bg-gray-700 dark:text-white",
              errors.name
                ? "border-red-500"
                : "border-gray-300 dark:border-gray-600"
            )}
            placeholder="Enter node name"
          />
          {errors.name && (
            <p className="mt-1 text-xs text-red-500">{errors.name}</p>
          )}
        </div>

        {/* Description */}
        <div>
          <label
            htmlFor="node-description"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Description
          </label>
          <textarea
            id="node-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className={cn(
              "w-full px-3 py-2 border rounded-lg text-sm resize-none",
              "focus:outline-none focus:ring-2 focus:ring-blue-500",
              "border-gray-300 dark:border-gray-600",
              "dark:bg-gray-700 dark:text-white"
            )}
            placeholder="Enter description (optional)"
          />
        </div>

        {/* Parent Selection */}
        <div>
          <label
            htmlFor="node-parent"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Parent Node
          </label>
          <select
            id="node-parent"
            value={parentId ?? ""}
            onChange={(e) => setParentId(e.target.value || null)}
            className={cn(
              "w-full px-3 py-2 border rounded-lg text-sm",
              "focus:outline-none focus:ring-2 focus:ring-blue-500",
              "border-gray-300 dark:border-gray-600",
              "dark:bg-gray-700 dark:text-white"
            )}
          >
            <option value="">No parent (root level)</option>
            {availableParents.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* Metadata (read-only for existing nodes) */}
        {node && !isNew && (
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-3">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Metadata
            </h4>

            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <FileText className="w-4 h-4" />
              <span>{node.metadata.documentsCount} documents</span>
            </div>

            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <Calendar className="w-4 h-4" />
              <span>
                Created: {new Date(node.metadata.createdAt).toLocaleDateString()}
              </span>
            </div>

            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <User className="w-4 h-4" />
              <span>By: {node.metadata.createdBy}</span>
            </div>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            {isNew ? "Create" : "Save Changes"}
          </button>
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            Cancel
          </button>
        </div>

        {!isNew && (
          <div className="flex gap-2">
            <button
              onClick={onAddChild}
              className="flex-1 flex items-center justify-center gap-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Child
            </button>
            <button
              onClick={onDelete}
              className="flex items-center justify-center gap-1 px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 border border-red-300 dark:border-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </button>
          </div>
        )}
      </div>
    </div>
  )
})

// Helper function to check if targetId is a descendant of nodeId
function isDescendant(
  nodeId: string,
  targetId: string,
  allNodes: TaxonomyNode[]
): boolean {
  const nodeMap = new Map(allNodes.map((n) => [n.id, n]))
  const node = nodeMap.get(nodeId)
  if (!node) return false

  const checkChildren = (childIds: string[]): boolean => {
    for (const childId of childIds) {
      if (childId === targetId) return true
      const child = nodeMap.get(childId)
      if (child && checkChildren(child.children)) return true
    }
    return false
  }

  return checkChildren(node.children)
}
