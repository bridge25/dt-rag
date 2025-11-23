/**
 * Type definitions for Taxonomy Builder
 *
 * @CODE:TAXONOMY-BUILDER-001
 */

export interface TaxonomyNode {
  id: string
  name: string
  description?: string
  parentId: string | null
  children: string[]
  metadata: {
    documentsCount: number
    createdAt: string
    updatedAt: string
    createdBy: string
  }
  position?: { x: number; y: number }
}

export interface TaxonomyAction {
  type: "add" | "update" | "delete" | "move"
  nodeId: string
  payload: Partial<TaxonomyNode> | null
  previousState: Partial<TaxonomyNode> | null
  timestamp: number
}

export type ViewMode = "tree" | "graph"
export type KeyboardMode = "navigation" | "editing" | "search"

export interface BuilderState {
  nodes: Map<string, TaxonomyNode>
  selectedNodeId: string | null
  viewMode: ViewMode
  undoStack: TaxonomyAction[]
  redoStack: TaxonomyAction[]
  isDirty: boolean
  isLoading: boolean
  isSaving: boolean
  lastSavedAt: Date | null
  error: string | null
}

export interface BuilderActions {
  // Node operations
  addNode: (node: Omit<TaxonomyNode, "id" | "children" | "metadata">) => string
  updateNode: (id: string, updates: Partial<TaxonomyNode>) => void
  deleteNode: (id: string) => void
  moveNode: (id: string, newParentId: string | null) => void

  // Selection
  setSelectedNode: (id: string | null) => void

  // View
  setViewMode: (mode: ViewMode) => void

  // Undo/Redo
  undo: () => void
  redo: () => void
  canUndo: () => boolean
  canRedo: () => boolean

  // Persistence
  save: () => Promise<void>
  loadTaxonomy: (taxonomyId: string) => Promise<void>
  reset: () => void

  // State
  setError: (error: string | null) => void
  setLoading: (loading: boolean) => void
}

export type TaxonomyBuilderStore = BuilderState & BuilderActions

export interface TaxonomyBuilderProps {
  taxonomyId: string
  initialData?: TaxonomyNode[]
  onSave?: (nodes: TaxonomyNode[]) => Promise<void>
  readOnly?: boolean
  className?: string
}

export interface NodeEditorProps {
  node: TaxonomyNode | null
  allNodes: TaxonomyNode[]
  onSave: (updates: Partial<TaxonomyNode>) => void
  onCancel: () => void
  onDelete: () => void
  onAddChild: () => void
  isNew?: boolean
}

export interface ActionToolbarProps {
  onAddNode: () => void
  onSave: () => void
  onUndo: () => void
  onRedo: () => void
  canUndo: boolean
  canRedo: boolean
  isDirty: boolean
  isSaving: boolean
  viewMode: ViewMode
  onViewModeChange: (mode: ViewMode) => void
}
