"use client"

/**
 * ActionToolbar - Top toolbar for Taxonomy Builder
 * Ethereal Glass Aesthetic
 *
 * @CODE:TAXONOMY-BUILDER-002
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
    <div className="flex items-center justify-between p-3 border-b border-white/10 bg-white/5 backdrop-blur-md">
      {/* Left: Action buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={onAddNode}
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-blue-600/80 hover:bg-blue-600 rounded-lg transition-all shadow-lg shadow-blue-500/20"
          aria-label="Add new node"
        >
          <Plus className="w-4 h-4" />
          Add Node
        </button>

        <div className="w-px h-6 bg-white/10 mx-2" />

        <button
          onClick={onUndo}
          disabled={!canUndo}
          className={cn(
            "p-2 rounded-lg transition-colors",
            canUndo
              ? "text-white/80 hover:bg-white/10 hover:text-white"
              : "text-white/20 cursor-not-allowed"
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
              ? "text-white/80 hover:bg-white/10 hover:text-white"
              : "text-white/20 cursor-not-allowed"
          )}
          aria-label="Redo"
          title="Redo (Ctrl+Y)"
        >
          <Redo2 className="w-5 h-5" />
        </button>
      </div>

      {/* Center: View mode toggle */}
      <div className="flex items-center gap-1 p-1 bg-black/20 rounded-lg border border-white/5">
        <button
          onClick={() => onViewModeChange("tree")}
          className={cn(
            "flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded-md transition-all",
            viewMode === "tree"
              ? "bg-white/10 text-white shadow-sm border border-white/10"
              : "text-white/40 hover:text-white/80 hover:bg-white/5"
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
            "flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded-md transition-all",
            viewMode === "graph"
              ? "bg-white/10 text-white shadow-sm border border-white/10"
              : "text-white/40 hover:text-white/80 hover:bg-white/5"
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
          <span className="text-sm text-amber-400 animate-pulse">
            Unsaved changes
          </span>
        )}
        <button
          onClick={onSave}
          disabled={!isDirty || isSaving}
          className={cn(
            "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all",
            isDirty && !isSaving
              ? "text-white bg-green-600/80 hover:bg-green-600 shadow-lg shadow-green-500/20"
              : "text-white/20 bg-white/5 cursor-not-allowed border border-white/5"
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
