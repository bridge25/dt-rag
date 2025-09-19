export interface TaxonomyNode {
  node_id: string
  label: string
  canonical_path: string[]
  version: string
  confidence: number
  document_count?: number
  description?: string
  metadata?: Record<string, any>
  created_at?: string
  updated_at?: string
  depth?: number
  parent_id?: string
}

export interface TaxonomyEdge {
  parent: string
  child: string
  version: string
  edge_type?: 'hierarchical' | 'cross_reference'
  confidence?: number
}

export interface TaxonomyTree {
  version: string
  total_nodes: number
  total_documents: number
  total_edges?: number
  nodes: TaxonomyNode[]
  edges: TaxonomyEdge[]
  roots?: string[]
  last_updated?: string
  validation_status?: ValidationStatus
}

export interface ValidationStatus {
  is_valid: boolean
  errors: string[]
  warnings: string[]
  cycles: string[][]
  orphaned_nodes: string[]
}

export interface TaxonomyVersion {
  version: string
  status: 'stable' | 'beta' | 'deprecated'
  description: string
  created_at: string
  node_count?: number
  document_count?: number
}

export interface VersionDiff {
  version_from: string
  version_to: string
  changes: VersionChange[]
  summary: {
    added: number
    removed: number
    modified: number
    moved: number
  }
}

export interface VersionChange {
  type: 'added' | 'removed' | 'modified' | 'moved'
  node_id: string
  path: string[]
  old_value?: any
  new_value?: any
  description: string
}

// HITL (Human-in-the-Loop) Types
export interface ClassificationQueueItem {
  id: string
  text: string
  suggested_path: string[]
  confidence: number
  status: 'pending' | 'approved' | 'rejected' | 'modified'
  human_reviewer?: string
  created_at: string
  reviewed_at?: string
  correction?: string
  reason?: string
}

export interface BatchOperation {
  type: 'approve_all' | 'reject_all' | 'approve_high_confidence'
  items: string[]
  reviewer: string
  notes?: string
}

// Performance and Metrics Types
export interface PerformanceMetrics {
  render_time: number
  virtual_items_count: number
  memory_usage: number
  fps: number
  last_measured: string
}

export interface TreeMetrics {
  total_nodes: number
  visible_nodes: number
  expanded_nodes: number
  max_depth: number
  avg_children_per_node: number
  load_time: number
}

// Search and Filter Types
export interface SearchFilters {
  canonical_in?: string[][]
  confidence_min?: number
  confidence_max?: number
  document_count_min?: number
  has_children?: boolean
  depth_max?: number
}

export interface TreeViewState {
  expandedNodes: Set<string>
  selectedNode: string | null
  focusedIndex: number
  searchQuery: string
  filters: SearchFilters
}

export interface TreeViewActions {
  toggleNode: (nodeId: string) => void
  selectNode: (nodeId: string) => void
  setFocusedIndex: (index: number) => void
  setSearchQuery: (query: string) => void
  setFilters: (filters: SearchFilters) => void
  expandAll: () => void
  collapseAll: () => void
  expandToNode: (nodeId: string) => void
}