export interface Document {
  id: string
  title: string
  content: string
  source_url?: string
  source_type: 'file' | 'url' | 'api'
  file_type?: string
  file_size?: number
  hash?: string
  status: DocumentStatus
  created_at: string
  updated_at: string
  processed_at?: string
  metadata?: DocumentMetadata
  chunks?: DocumentChunk[]
  classification?: DocumentClassification
}

export type DocumentStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'reprocessing'

export interface DocumentMetadata {
  author?: string
  language?: string
  keywords?: string[]
  category?: string
  tags?: string[]
  custom_fields?: Record<string, any>
}

export interface DocumentChunk {
  chunk_id: string
  document_id: string
  text: string
  chunk_index: number
  token_count: number
  embedding?: number[]
  classification_results?: ChunkClassification[]
  created_at: string
}

export interface ChunkClassification {
  taxonomy_path: string[]
  confidence: number
  model_version: string
  classification_type: 'rule' | 'ml' | 'hybrid'
  created_at: string
}

export interface DocumentClassification {
  primary_path: string[]
  confidence: number
  alternative_paths?: Array<{
    path: string[]
    confidence: number
  }>
  model_version: string
  classification_type: 'rule' | 'ml' | 'hybrid'
  created_at: string
  human_validated?: boolean
  human_validator?: string
}

export interface UploadRequest {
  files?: File[]
  urls?: string[]
  metadata?: DocumentMetadata
  auto_classify?: boolean
  chunk_strategy?: ChunkingStrategy
}

export interface ChunkingStrategy {
  method: 'fixed_size' | 'sentence' | 'paragraph' | 'semantic'
  chunk_size?: number
  overlap_size?: number
  separator?: string
}

export interface UploadResponse {
  job_id: string
  status: string
  message: string
  documents?: Array<{
    id: string
    title: string
    status: DocumentStatus
  }>
}

export interface IngestionJob {
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  total_documents: number
  processed_documents: number
  failed_documents: number
  created_at: string
  completed_at?: string
  error_message?: string
  results?: IngestionResult[]
}

export interface IngestionResult {
  document_id: string
  title: string
  status: DocumentStatus
  chunks_created: number
  classification_results?: DocumentClassification
  error_message?: string
  processing_time: number
}

export interface DocumentFilter {
  status?: DocumentStatus[]
  source_type?: string[]
  file_type?: string[]
  date_from?: string
  date_to?: string
  has_classification?: boolean
  taxonomy_path?: string[]
}

export interface DocumentSearchRequest {
  query?: string
  filters?: DocumentFilter
  sort_by?: 'created_at' | 'updated_at' | 'title' | 'relevance'
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

export interface DocumentSearchResponse {
  documents: Document[]
  total_count: number
  page: number
  page_size: number
  total_pages: number
}