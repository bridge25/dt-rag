export interface TaxonomyNode {
  node_id: string
  label: string
  canonical_path: string[]
  version: string
  confidence: number
  document_count?: number
}

export interface TaxonomyEdge {
  parent: string
  child: string
  version: string
}

export interface TaxonomyTree {
  version: string
  total_nodes: number
  total_documents: number
  nodes: TaxonomyNode[]
  edges: TaxonomyEdge[]
}

export interface ApiResponse<T> {
  data: T
  success: boolean
  message?: string
}

export interface ErrorResponse {
  code: string              // e.g., "FORBIDDEN", "RATE_LIMITED", "INVALID_INPUT"
  message: string
  request_id?: string       // For debugging and support
  details?: Record<string, any>  // Additional error context
}