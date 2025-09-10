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
  error: string
  message: string
  statusCode: number
}