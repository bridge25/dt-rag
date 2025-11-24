"use client"

/**
 * ActionToolbar - Top toolbar for Taxonomy Builder
 *
 * @CODE:TAXONOMY-BUILDER-001
 */

import { memo } from "react"
import { cn } from "@/lib/utils"
import {
  Plus,
  Save,
  Undo2,
  Redo2,
  LayoutGrid,
  Network,
  Loader2,
} from "lucide-react"
import type { ActionToolbarProps } from "./types"

export const ActionToolbar = memo<ActionToolbarProps>(function ActionToolbar({
  onAddNode,
  onSave,
  onUndo,
  onRedo,
  canUndo,
  canRedo,
  isDirty,
  isSaving,
  viewMode,
  onViewModeChange,
}) {
  return (
    <div className="flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      {/* Left: Action buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={onAddNode}
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          aria-label="Add new node"
        >
          <Plus className="w-4 h-4" />
          Add Node
        </button>

        <div className="w-px h-6 bg-gray-200 dark:bg-gray-600 mx-2" />

        <button
          onClick={onUndo}
          disabled={!canUndo}
          className={cn(
            "p-2 rounded-lg transition-colors",
            canUndo
              ? "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              : "text-gray-300 dark:text-gray-600 cursor-not-allowed"
          )}
          aria-label="Undo"
          title="Undo (Ctrl+Z)"
        >
          <Undo2 className="w-5 h-5" />
        </button>

        <button
          onClick={onRedo}
          disabled={!canRedo}
          className={cn(
            "p-2 rounded-lg transition-colors",
            canRedo
              ? "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              : "text-gray-300 dark:text-gray-600 cursor-not-allowed"
          )}
          aria-label="Redo"
          title="Redo (Ctrl+Y)"
        >
          <Redo2 className="w-5 h-5" />
        </button>
      </div>

      {/* Center: View mode toggle */}
      <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-700 rounded-lg">
        <button
          onClick={() => onViewModeChange("tree")}
          className={cn(
            "flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
            viewMode === "tree"
              ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
              : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          )}
          aria-label="Tree view"
          aria-pressed={viewMode === "tree"}
        >
          <LayoutGrid className="w-4 h-4" />
          Tree
        </button>
        <button
          onClick={() => onViewModeChange("graph")}
          className={cn(
            "flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
            viewMode === "graph"
              ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
              : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          )}
          aria-label="Graph view"
          aria-pressed={viewMode === "graph"}
        >
          <Network className="w-4 h-4" />
          Graph
        </button>
      </div>

      {/* Right: Save button */}
      <div className="flex items-center gap-3">
        {isDirty && (
          <span className="text-sm text-amber-600 dark:text-amber-400">
            Unsaved changes
          </span>
        )}
        <button
          onClick={onSave}
          disabled={!isDirty || isSaving}
          className={cn(
            "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors",
            isDirty && !isSaving
              ? "text-white bg-green-600 hover:bg-green-700"
              : "text-gray-400 bg-gray-100 dark:bg-gray-700 cursor-not-allowed"
          )}
          aria-label="Save taxonomy"
        >
          {isSaving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          {isSaving ? "Saving..." : "Save"}
        </button>
      </div>
    </div>
  )
})
