"use client"

/**
 * DraggableTreeNode - A tree node with drag-and-drop capability
 *
 * @CODE:TAXONOMY-BUILDER-001
 */

import { memo, type ReactNode } from "react"
import { useDraggable, useDroppable } from "@dnd-kit/core"
import { CSS } from "@dnd-kit/utilities"
import { cn } from "@/lib/utils"
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  GripVertical,
} from "lucide-react"
import type { TaxonomyNode } from "./types"

export interface DraggableTreeNodeProps {
  node: TaxonomyNode
  depth: number
  isExpanded: boolean
  isSelected: boolean
  isDropTarget: boolean
  isDragging: boolean
  children?: ReactNode
  hasChildren: boolean
  documentsCount: number
  onSelect: () => void
  onToggleExpand: () => void
  readOnly?: boolean
}

export const DraggableTreeNode = memo<DraggableTreeNodeProps>(
  function DraggableTreeNode({
    node,
    depth,
    isExpanded,
    isSelected,
    isDropTarget,
    isDragging,
    children,
    hasChildren,
    documentsCount,
    onSelect,
    onToggleExpand,
    readOnly = false,
  }) {
    const {
      attributes,
      listeners,
      setNodeRef: setDragRef,
      transform,
    } = useDraggable({
      id: node.id,
      disabled: readOnly,
      data: { node },
    })

    const { setNodeRef: setDropRef, isOver } = useDroppable({
      id: `drop-${node.id}`,
      disabled: readOnly,
      data: { node },
    })

    // Extract and ignore conflicting attributes from dnd-kit
    const { role: _role, tabIndex: _tabIndex, ...safeAttributes } = attributes

    return (
      <div ref={setDropRef}>
        <div
          ref={setDragRef}
          role="treeitem"
          tabIndex={0}
          onClick={onSelect}
          onDoubleClick={() => hasChildren && onToggleExpand()}
          onKeyDown={(e) => {
            if (e.key === "Enter") onSelect()
            if (e.key === " " && hasChildren) {
              e.preventDefault()
              onToggleExpand()
            }
          }}
          className={cn(
            "flex items-center gap-2 px-3 py-2 cursor-pointer rounded-md transition-colors group",
            "hover:bg-gray-100 dark:hover:bg-gray-700",
            isSelected && "bg-blue-50 dark:bg-blue-900/30 border-l-2 border-blue-500",
            isOver && !isDragging && "bg-green-50 dark:bg-green-900/30 border-2 border-dashed border-green-500",
            isDropTarget && "ring-2 ring-blue-400",
            isDragging && "opacity-50 cursor-grabbing"
          )}
          style={{
            paddingLeft: `${depth * 20 + 12}px`,
            ...(transform ? { transform: CSS.Translate.toString(transform), opacity: isDragging ? 0.5 : 1 } : {}),
          }}
          aria-selected={isSelected}
          {...safeAttributes}
        >
          {/* Drag handle */}
          {!readOnly && (
            <div
              {...listeners}
              className="p-1 rounded cursor-grab opacity-0 group-hover:opacity-100 transition-opacity hover:bg-gray-200 dark:hover:bg-gray-600"
              onClick={(e) => e.stopPropagation()}
            >
              <GripVertical className="w-3 h-3 text-gray-400" />
            </div>
          )}

          {/* Expand/Collapse button */}
          <button
            onClick={(e) => {
              e.stopPropagation()
              onToggleExpand()
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
          {documentsCount > 0 && (
            <span className="px-1.5 py-0.5 text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded">
              {documentsCount}
            </span>
          )}
        </div>

        {/* Children */}
        {isExpanded && hasChildren && <div>{children}</div>}
      </div>
    )
  }
)

/**
 * DragOverlay node - rendered during drag operation
 */
export interface DragOverlayNodeProps {
  node: TaxonomyNode
}

export const DragOverlayNode = memo<DragOverlayNodeProps>(
  function DragOverlayNode({ node }) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-600">
        <Folder className="w-4 h-4 text-amber-500" />
        <span className="text-sm text-gray-900 dark:text-white">
          {node.name}
        </span>
      </div>
    )
  }
)

/**
 * Root drop zone - for dropping nodes to make them root level
 */
export interface RootDropZoneProps {
  isOver: boolean
}

export const RootDropZone = memo<RootDropZoneProps>(function RootDropZone({
  isOver,
}) {
  const { setNodeRef } = useDroppable({
    id: "drop-root",
    data: { isRoot: true },
  })

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "h-8 mx-4 my-2 rounded-md border-2 border-dashed transition-colors flex items-center justify-center",
        isOver
          ? "border-green-500 bg-green-50 dark:bg-green-900/20"
          : "border-gray-200 dark:border-gray-700"
      )}
    >
      <span className="text-xs text-gray-400">Drop here to make root node</span>
    </div>
  )
})
