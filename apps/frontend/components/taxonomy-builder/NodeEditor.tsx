"use client"

/**
 * NodeEditor - Side panel for editing node properties
 * Ethereal Glass Aesthetic
 *
 * @CODE:TAXONOMY-BUILDER-002
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
      <div className="w-80 border-l border-white/10 bg-white/5 backdrop-blur-md p-6 flex items-center justify-center">
        <p className="text-white/40 text-center">
          Select a node to view details
        </p>
      </div>
    )
  }

  return (
    <div className="w-80 border-l border-white/10 bg-white/5 backdrop-blur-md flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <h3 className="text-lg font-semibold text-white">
          {isNew ? "New Node" : "Edit Node"}
        </h3>
        <button
          onClick={onCancel}
          className="p-1 text-white/40 hover:text-white rounded transition-colors"
          aria-label="Close panel"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Form */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {/* Name */}
        <div>
          <label
            htmlFor="node-name"
            className="block text-sm font-medium text-white/80 mb-1"
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
              "w-full px-3 py-2 border rounded-lg text-sm bg-white/5 text-white placeholder:text-white/20",
              "focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50",
              errors.name
                ? "border-red-500/50"
                : "border-white/10"
            )}
            placeholder="Enter node name"
          />
          {errors.name && (
            <p className="mt-1 text-xs text-red-400">{errors.name}</p>
          )}
        </div>

        {/* Description */}
        <div>
          <label
            htmlFor="node-description"
            className="block text-sm font-medium text-white/80 mb-1"
          >
            Description
          </label>
          <textarea
            id="node-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className={cn(
              "w-full px-3 py-2 border rounded-lg text-sm resize-none bg-white/5 text-white placeholder:text-white/20",
              "focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50",
              "border-white/10"
            )}
            placeholder="Enter description (optional)"
          />
        </div>

        {/* Parent Selection */}
        <div>
          <label
            htmlFor="node-parent"
            className="block text-sm font-medium text-white/80 mb-1"
          >
            Parent Node
          </label>
          <select
            id="node-parent"
            value={parentId ?? ""}
            onChange={(e) => setParentId(e.target.value || null)}
            className={cn(
              "w-full px-3 py-2 border rounded-lg text-sm bg-dark-navy text-white",
              "focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50",
              "border-white/10"
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
          <div className="pt-4 border-t border-white/10 space-y-3">
            <h4 className="text-sm font-medium text-white/80">
              Metadata
            </h4>

            <div className="flex items-center gap-2 text-sm text-white/60">
              <FileText className="w-4 h-4" />
              <span>{node.metadata.documentsCount} documents</span>
            </div>

            <div className="flex items-center gap-2 text-sm text-white/60">
              <Calendar className="w-4 h-4" />
              <span>
                Created: {new Date(node.metadata.createdAt).toLocaleDateString()}
              </span>
            </div>

            <div className="flex items-center gap-2 text-sm text-white/60">
              <User className="w-4 h-4" />
              <span>By: {node.metadata.createdBy}</span>
            </div>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-white/10 space-y-2 bg-white/5">
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors shadow-lg shadow-blue-500/20"
          >
            {isNew ? "Create" : "Save Changes"}
          </button>
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-white/80 bg-white/10 hover:bg-white/20 rounded-lg transition-colors border border-white/10"
          >
            Cancel
          </button>
        </div>

        {!isNew && (
          <div className="flex gap-2">
            <button
              onClick={onAddChild}
              className="flex-1 flex items-center justify-center gap-1 px-4 py-2 text-sm font-medium text-white/80 border border-white/20 rounded-lg hover:bg-white/10 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Child
            </button>
            <button
              onClick={onDelete}
              className="flex items-center justify-center gap-1 px-4 py-2 text-sm font-medium text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/10 transition-colors"
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
