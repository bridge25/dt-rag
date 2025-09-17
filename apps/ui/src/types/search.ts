export interface SearchRequest {
  q: string
  filters?: Record<string, any>
  bm25_topk?: number
  vector_topk?: number
  rerank_candidates?: number
  final_topk?: number
}

export interface SearchHit {
  chunk_id: string
  score: number
  text?: string
  taxonomy_path?: string[]
  source?: {
    title?: string
    source_url?: string
    search_type?: string
    [key: string]: any
  }
  highlights?: SearchHighlight[]
  document_id?: string
  timestamp?: string
}

export interface SearchHighlight {
  field: string
  fragments: string[]
}

export interface SearchResponse {
  hits: SearchHit[]
  latency: number
  request_id: string
  total_candidates?: number
  sources_count?: number
  taxonomy_version: string
  aggregations?: SearchAggregations
  suggestions?: string[]
}

export interface SearchAggregations {
  taxonomy_paths?: Array<{
    path: string[]
    count: number
  }>
  sources?: Array<{
    source: string
    count: number
  }>
  confidence_ranges?: Array<{
    range: string
    count: number
  }>
}

export interface SearchState {
  query: string
  results: SearchHit[]
  loading: boolean
  error: string | null
  filters: SearchFilters
  facets: SearchFacets
  totalResults: number
  page: number
  pageSize: number
}

export interface SearchFilters {
  taxonomy_paths?: string[][]
  sources?: string[]
  confidence_min?: number
  confidence_max?: number
  date_from?: string
  date_to?: string
  document_types?: string[]
}

export interface SearchFacets {
  taxonomy_paths: Array<{
    path: string[]
    count: number
    selected: boolean
  }>
  sources: Array<{
    name: string
    count: number
    selected: boolean
  }>
  document_types: Array<{
    type: string
    count: number
    selected: boolean
  }>
}

export interface SavedSearch {
  id: string
  name: string
  query: string
  filters: SearchFilters
  created_at: string
  created_by: string
  description?: string
  is_public?: boolean
}

export interface SearchMetrics {
  total_searches: number
  avg_latency: number
  popular_queries: Array<{
    query: string
    count: number
    avg_results: number
  }>
  error_rate: number
  last_updated: string
}