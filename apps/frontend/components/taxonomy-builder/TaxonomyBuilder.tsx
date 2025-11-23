"use client"

/**
 * TaxonomyBuilder - Main container component for taxonomy editing
 *
 * @CODE:TAXONOMY-BUILDER-001
 */

import { useEffect, useCallback, useState } from "react"
import { cn } from "@/lib/utils"
import { useTaxonomyBuilderStore } from "@/stores/useTaxonomyBuilderStore"
import { ActionToolbar } from "./ActionToolbar"
import { NodeEditor } from "./NodeEditor"
import type { TaxonomyBuilderProps, TaxonomyNode } from "./types"
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  AlertCircle,
} from "lucide-react"

export function TaxonomyBuilder({
  taxonomyId,
  initialData,
  readOnly = false,
  className,
}: TaxonomyBuilderProps) {
  const store = useTaxonomyBuilderStore()
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [isCreatingNew, setIsCreatingNew] = useState(false)
  const [newNodeParentId, setNewNodeParentId] = useState<string | null>(null)

  // Load taxonomy on mount
  useEffect(() => {
    if (taxonomyId) {
      store.loadTaxonomy(taxonomyId)
    }
    return () => store.reset()
  }, [taxonomyId])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return
      }

      if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) {
        e.preventDefault()
        store.undo()
      } else if ((e.ctrlKey || e.metaKey) && (e.key === "y" || (e.key === "z" && e.shiftKey))) {
        e.preventDefault()
        store.redo()
      } else if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault()
        if (store.isDirty) {
          store.save()
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [store])

  // Convert Map to array for rendering
  const nodesArray = Array.from(store.nodes.values())

  // Get root nodes (no parent)
  const rootNodes = nodesArray.filter((n) => n.parentId === null)

  const toggleExpand = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev)
      if (next.has(nodeId)) {
        next.delete(nodeId)
      } else {
        next.add(nodeId)
      }
      return next
    })
  }, [])

  const handleAddNode = useCallback(() => {
    setIsCreatingNew(true)
    setNewNodeParentId(store.selectedNodeId)
    store.setSelectedNode(null)
  }, [store])

  const handleAddChild = useCallback(() => {
    if (store.selectedNodeId) {
      setIsCreatingNew(true)
      setNewNodeParentId(store.selectedNodeId)
      setExpandedNodes((prev) => {
        const next = new Set(Array.from(prev))
        next.add(store.selectedNodeId!)
        return next
      })
    }
  }, [store.selectedNodeId])

  const handleSaveNewNode = useCallback(
    (data: Partial<TaxonomyNode>) => {
      store.addNode({
        name: data.name ?? "New Node",
        description: data.description,
        parentId: newNodeParentId,
      })
      setIsCreatingNew(false)
      setNewNodeParentId(null)
    },
    [store, newNodeParentId]
  )

  const handleCancelNew = useCallback(() => {
    setIsCreatingNew(false)
    setNewNodeParentId(null)
  }, [])

  const handleSaveNode = useCallback(
    (updates: Partial<TaxonomyNode>) => {
      if (store.selectedNodeId) {
        store.updateNode(store.selectedNodeId, updates)
      }
    },
    [store]
  )

  const handleDeleteNode = useCallback(() => {
    if (store.selectedNodeId) {
      const node = store.nodes.get(store.selectedNodeId)
      const hasChildren = node && node.children.length > 0

      if (hasChildren) {
        const confirmed = window.confirm(
          `This will delete the node and all ${node.children.length} child node(s). Are you sure?`
        )
        if (!confirmed) return
      }

      store.deleteNode(store.selectedNodeId)
    }
  }, [store])

  const selectedNode = store.selectedNodeId
    ? store.nodes.get(store.selectedNodeId) ?? null
    : null

  // Render tree node recursively
  const renderNode = (node: TaxonomyNode, depth: number = 0) => {
    const hasChildren = node.children.length > 0
    const isExpanded = expandedNodes.has(node.id)
    const isSelected = store.selectedNodeId === node.id
    const childNodes = node.children
      .map((id) => store.nodes.get(id))
      .filter(Boolean) as TaxonomyNode[]

    return (
      <div key={node.id}>
        <div
          role="button"
          tabIndex={0}
          onClick={() => store.setSelectedNode(node.id)}
          onDoubleClick={() => hasChildren && toggleExpand(node.id)}
          onKeyDown={(e) => {
            if (e.key === "Enter") store.setSelectedNode(node.id)
            if (e.key === " " && hasChildren) {
              e.preventDefault()
              toggleExpand(node.id)
            }
          }}
          className={cn(
            "flex items-center gap-2 px-3 py-2 cursor-pointer rounded-md transition-colors",
            "hover:bg-gray-100 dark:hover:bg-gray-700",
            isSelected && "bg-blue-50 dark:bg-blue-900/30 border-l-2 border-blue-500"
          )}
          style={{ paddingLeft: `${depth * 20 + 12}px` }}
          aria-selected={isSelected}
        >
          {/* Expand/Collapse button */}
          <button
            onClick={(e) => {
              e.stopPropagation()
              toggleExpand(node.id)
            }}
            className={cn(
              "p-0.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600",
              !hasChildren && "invisible"
            )}
            aria-label={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-500" />
            )}
          </button>

          {/* Folder icon */}
          {isExpanded && hasChildren ? (
            <FolderOpen className="w-4 h-4 text-amber-500" />
          ) : (
            <Folder className="w-4 h-4 text-amber-500" />
          )}

          {/* Node name */}
          <span className="flex-1 text-sm text-gray-900 dark:text-white truncate">
            {node.name}
          </span>

          {/* Document count badge */}
          {node.metadata.documentsCount > 0 && (
            <span className="px-1.5 py-0.5 text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded">
              {node.metadata.documentsCount}
            </span>
          )}
        </div>

        {/* Children */}
        {isExpanded && hasChildren && (
          <div>
            {childNodes.map((child) => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  if (store.isLoading) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  return (
    <div className={cn("flex flex-col h-full bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden", className)}>
      {/* Error Banner */}
      {store.error && (
        <div className="flex items-center gap-2 px-4 py-2 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
          <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
          <span className="text-sm text-red-600 dark:text-red-400">{store.error}</span>
          <button
            onClick={() => store.setError(null)}
            className="ml-auto text-sm text-red-600 dark:text-red-400 underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Toolbar */}
      {!readOnly && (
        <ActionToolbar
          onAddNode={handleAddNode}
          onSave={() => store.save()}
          onUndo={() => store.undo()}
          onRedo={() => store.redo()}
          canUndo={store.canUndo()}
          canRedo={store.canRedo()}
          isDirty={store.isDirty}
          isSaving={store.isSaving}
          viewMode={store.viewMode}
          onViewModeChange={store.setViewMode}
        />
      )}

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Tree View */}
        <div className="flex-1 overflow-y-auto p-4">
          {rootNodes.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Folder className="w-16 h-16 text-gray-300 dark:text-gray-600 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No taxonomy nodes yet
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                Click "Add Node" to create your first category
              </p>
              {!readOnly && (
                <button
                  onClick={handleAddNode}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
                >
                  Add First Node
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-1">
              {rootNodes.map((node) => renderNode(node))}
            </div>
          )}
        </div>

        {/* Side Panel */}
        {!readOnly && (
          <NodeEditor
            node={isCreatingNew ? null : selectedNode}
            allNodes={nodesArray}
            onSave={isCreatingNew ? handleSaveNewNode : handleSaveNode}
            onCancel={isCreatingNew ? handleCancelNew : () => store.setSelectedNode(null)}
            onDelete={handleDeleteNode}
            onAddChild={handleAddChild}
            isNew={isCreatingNew}
          />
        )}
      </div>

      {/* Status Bar */}
      <div className="flex items-center justify-between px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-sm">
        <span className="text-gray-500 dark:text-gray-400">
          {nodesArray.length} nodes
        </span>
        {store.lastSavedAt && (
          <span className="text-gray-500 dark:text-gray-400">
            Last saved: {store.lastSavedAt.toLocaleTimeString()}
          </span>
        )}
      </div>
    </div>
  )
}
