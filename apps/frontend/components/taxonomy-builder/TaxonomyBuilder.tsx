"use client"

/**
 * TaxonomyBuilder - Main container component for taxonomy editing
 * Ethereal Glass Aesthetic
 *
 * @CODE:TAXONOMY-BUILDER-002
 */

import { useEffect, useCallback, useState } from "react"
import {
  DndContext,
  DragOverlay,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragStartEvent,
  type DragEndEvent,
  type DragOverEvent,
} from "@dnd-kit/core"
import { cn } from "@/lib/utils"
import { useTaxonomyBuilderStore } from "@/stores/useTaxonomyBuilderStore"
import { ActionToolbar } from "./ActionToolbar"
import { NodeEditor } from "./NodeEditor"
import {
  DraggableTreeNode,
  DragOverlayNode,
  RootDropZone,
} from "./DraggableTreeNode"
import { GraphView } from "./GraphView"
import type { TaxonomyBuilderProps, TaxonomyNode } from "./types"
import { Folder, AlertCircle, Plus } from "lucide-react"

export function TaxonomyBuilder({
  taxonomyId,
  readOnly = false,
  className,
}: TaxonomyBuilderProps) {
  const store = useTaxonomyBuilderStore()
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [isCreatingNew, setIsCreatingNew] = useState(false)
  const [newNodeParentId, setNewNodeParentId] = useState<string | null>(null)

  // Drag state
  const [activeId, setActiveId] = useState<string | null>(null)
  const [overId, setOverId] = useState<string | null>(null)

  // Configure drag sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px movement before drag starts
      },
    }),
    useSensor(KeyboardSensor)
  )

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
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return
      }

      if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) {
        e.preventDefault()
        store.undo()
      } else if (
        (e.ctrlKey || e.metaKey) &&
        (e.key === "y" || (e.key === "z" && e.shiftKey))
      ) {
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
      const next = new Set(Array.from(prev))
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

  // Drag handlers
  const handleDragStart = useCallback((event: DragStartEvent) => {
    const { active } = event
    setActiveId(active.id as string)
  }, [])

  const handleDragOver = useCallback((event: DragOverEvent) => {
    const { over } = event
    if (over) {
      // Extract the actual node id from "drop-{id}" format
      const overId = (over.id as string).replace("drop-", "")
      setOverId(overId === "root" ? null : overId)
    } else {
      setOverId(null)
    }
  }, [])

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event
      setActiveId(null)
      setOverId(null)

      if (!over) return

      const draggedNodeId = active.id as string
      const overIdRaw = over.id as string

      // Check if dropping on root zone
      if (overIdRaw === "drop-root") {
        // Move to root level
        store.moveNode(draggedNodeId, null)
        return
      }

      // Extract target node id
      const targetNodeId = overIdRaw.replace("drop-", "")

      // Don't drop on self
      if (draggedNodeId === targetNodeId) return

      // Move node to new parent
      store.moveNode(draggedNodeId, targetNodeId)

      // Auto-expand the target node to show the moved child
      setExpandedNodes((prev) => {
        const next = new Set(Array.from(prev))
        next.add(targetNodeId)
        return next
      })
    },
    [store]
  )

  const handleDragCancel = useCallback(() => {
    setActiveId(null)
    setOverId(null)
  }, [])

  const selectedNode = store.selectedNodeId
    ? store.nodes.get(store.selectedNodeId) ?? null
    : null

  const activeNode = activeId ? store.nodes.get(activeId) ?? null : null

  // Render tree node recursively
  const renderNode = (node: TaxonomyNode, depth: number = 0) => {
    const hasChildren = node.children.length > 0
    const isExpanded = expandedNodes.has(node.id)
    const isSelected = store.selectedNodeId === node.id
    const childNodes = node.children
      .map((id) => store.nodes.get(id))
      .filter(Boolean) as TaxonomyNode[]

    const isDragging = activeId === node.id
    const isDropTarget = overId === node.id

    return (
      <DraggableTreeNode
        key={node.id}
        node={node}
        depth={depth}
        isExpanded={isExpanded}
        isSelected={isSelected}
        isDropTarget={isDropTarget}
        isDragging={isDragging}
        hasChildren={hasChildren}
        documentsCount={node.metadata.documentsCount}
        onSelect={() => store.setSelectedNode(node.id)}
        onToggleExpand={() => toggleExpand(node.id)}
        readOnly={readOnly}
      >
        {childNodes.map((child) => renderNode(child, depth + 1))}
      </DraggableTreeNode>
    )
  }

  if (store.isLoading) {
    return (
      <div className={cn("flex items-center justify-center h-96 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md", className)}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400" />
      </div>
    )
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div
        className={cn(
          "flex flex-col h-full rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md overflow-hidden shadow-glass",
          className
        )}
      >
        {/* Error Banner */}
        {store.error && (
          <div className="flex items-center gap-2 px-4 py-2 bg-red-500/10 border-b border-red-500/20 backdrop-blur-sm">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <span className="text-sm text-red-400">
              {store.error}
            </span>
            <button
              onClick={() => store.setError(null)}
              className="ml-auto text-sm text-red-400 underline hover:text-red-300"
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
          {/* Tree View or Graph View based on viewMode */}
          {store.viewMode === "tree" ? (
            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
              {rootNodes.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="h-16 w-16 rounded-2xl bg-white/5 flex items-center justify-center mb-4 border border-white/10">
                    <Folder className="w-8 h-8 text-white/40" />
                  </div>
                  <h3 className="text-lg font-medium text-white mb-2">
                    No taxonomy nodes yet
                  </h3>
                  <p className="text-sm text-white/60 mb-6">
                    Click "Add Node" to create your first category
                  </p>
                  {!readOnly && (
                    <button
                      onClick={handleAddNode}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors shadow-lg shadow-blue-500/20"
                    >
                      <Plus className="w-4 h-4" />
                      Add First Node
                    </button>
                  )}
                </div>
              ) : (
                <div className="space-y-1">
                  {/* Root drop zone */}
                  {!readOnly && activeId && (
                    <RootDropZone isOver={overId === null && activeId !== null} />
                  )}
                  {rootNodes.map((node) => renderNode(node))}
                </div>
              )}
            </div>
          ) : (
            <GraphView
              nodes={store.nodes}
              selectedNodeId={store.selectedNodeId}
              onSelectNode={store.setSelectedNode}
              className="flex-1"
            />
          )}

          {/* Side Panel */}
          {!readOnly && (
            <NodeEditor
              node={isCreatingNew ? null : selectedNode}
              allNodes={nodesArray}
              onSave={isCreatingNew ? handleSaveNewNode : handleSaveNode}
              onCancel={
                isCreatingNew ? handleCancelNew : () => store.setSelectedNode(null)
              }
              onDelete={handleDeleteNode}
              onAddChild={handleAddChild}
              isNew={isCreatingNew}
            />
          )}
        </div>

        {/* Status Bar */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-white/10 bg-white/5 text-sm backdrop-blur-sm">
          <span className="text-white/40">
            {nodesArray.length} nodes
            {activeId && " • Dragging..."}
          </span>
          {store.lastSavedAt && (
            <span className="text-white/40">
              Last saved: {store.lastSavedAt.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Drag Overlay */}
      <DragOverlay>
        {activeNode ? <DragOverlayNode node={activeNode} /> : null}
      </DragOverlay>
    </DndContext>
  )
}
