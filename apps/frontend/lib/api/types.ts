import { z } from "zod"

// ============================================================================
// Common Models (from packages/common_schemas/common_schemas/models.py)
// ============================================================================

export const SourceMetaSchema = z.object({
  url: z.string(),
  title: z.string(),
  date: z.string(),
  author: z.string().optional(),
  content_type: z.string().optional(),
  language: z.string().optional(),
})

export const SearchHitSchema = z.object({
  chunk_id: z.string(),
  score: z.number(),
  text: z.string(),
  source: SourceMetaSchema,
  taxonomy_path: z.array(z.string()),
  highlights: z.array(z.string()).optional(),
  metadata: z.record(z.string(), z.any()).optional(),
})

export const SearchRequestSchema = z.object({
  q: z.string().min(1),
  max_results: z.number().min(1).max(100).default(10),
  canonical_in: z.array(z.array(z.string())).optional(),
  min_score: z.number().min(0).max(1).optional(),
  include_highlights: z.boolean().default(true),
  search_mode: z.string().optional().default("hybrid"),
})

export const SearchResponseSchema = z.object({
  hits: z.array(SearchHitSchema),
  latency: z.number(),
  request_id: z.string(),
  total_candidates: z.number().optional(),
  sources_count: z.number().optional(),
  taxonomy_version: z.string().optional(),
  query_analysis: z.record(z.string(), z.any()).optional(),
})

export const ClassificationResultSchema = z.object({
  taxonomy_path: z.array(z.string()),
  confidence: z.number(),
  alternatives: z.array(z.record(z.string(), z.union([z.array(z.string()), z.number()]))).optional(),
})

export const DocumentChunkSchema = z.object({
  chunk_id: z.string(),
  text: z.string(),
  start_char: z.number(),
  end_char: z.number(),
  metadata: z.record(z.string(), z.any()).optional(),
})

export const ProcessingStatusSchema = z.object({
  job_id: z.string(),
  status: z.string(),
  progress: z.number().optional(),
  message: z.string().optional(),
  created_at: z.string(),
  updated_at: z.string().optional(),
  completed_at: z.string().optional(),
})

export const ErrorDetailSchema = z.object({
  code: z.string(),
  message: z.string(),
  details: z.record(z.string(), z.any()).optional(),
  timestamp: z.string(),
})

export const TaxonomyNodeSchema: z.ZodType<{
  id: string
  name: string
  path: string[]
  parent_id: string | null
  children?: Array<{
    id: string
    name: string
    path: string[]
    parent_id: string | null
    children?: any[]
    metadata?: Record<string, any>
    level: number
  }>
  metadata?: Record<string, any>
  level: number
}> = z.object({
  id: z.string(),
  name: z.string(),
  path: z.array(z.string()),
  parent_id: z.string().nullable(),
  children: z.array(z.lazy(() => TaxonomyNodeSchema)).optional(),
  metadata: z.record(z.string(), z.any()).optional(),
  level: z.number(),
})

export const ClassifyRequestSchema = z.object({
  text: z.string().min(1),
  max_suggestions: z.number().min(1).max(20).default(5),
  include_confidence: z.boolean().default(true),
  taxonomy_filter: z.array(z.string()).optional(),
})

export const ClassifyResponseSchema = z.object({
  classifications: z.array(ClassificationResultSchema),
  request_id: z.string(),
  processing_time: z.number(),
  taxonomy_version: z.string().optional(),
})

export const FromCategoryRequestSchema = z.object({
  category_path: z.array(z.string()),
  config: z.record(z.string(), z.any()).optional(),
  features: z.record(z.string(), z.boolean()).optional(),
})

export const RetrievalConfigSchema = z.object({
  max_results: z.number().min(1).max(100).default(10),
  similarity_threshold: z.number().min(0).max(1).default(0.7),
  rerank_enabled: z.boolean().default(true),
  include_metadata: z.boolean().default(true),
})

export const FeaturesConfigSchema = z.object({
  semantic_search: z.boolean().default(true),
  keyword_search: z.boolean().default(true),
  classification: z.boolean().default(true),
  summarization: z.boolean().default(false),
  qa_mode: z.boolean().default(false),
})

export const AgentManifestSchema = z.object({
  name: z.string(),
  description: z.string(),
  taxonomy_scope: z.array(z.string()),
  retrieval_config: RetrievalConfigSchema,
  features_config: FeaturesConfigSchema,
  created_at: z.string(),
  version: z.string().default("1.0.0"),
})

// ============================================================================
// Agent Factory Models (from apps/api/routers/agent_factory_router.py)
// ============================================================================

export const AgentCreateResponseSchema = z.object({
  agent_id: z.string(),
  name: z.string(),
  status: z.string(),
  capabilities: z.array(z.string()),
  created_at: z.string(),
})

export const AgentStatusSchema = z.object({
  agent_id: z.string(),
  name: z.string(),
  status: z.string(),
  created_at: z.string(),
  last_used: z.string().optional(),
  usage_count: z.number().default(0),
  performance_metrics: z.record(z.string(), z.number()),
})

export const AgentMetricsSchema = z.object({
  total_requests: z.number(),
  avg_response_time_ms: z.number(),
  success_rate: z.number(),
  user_satisfaction: z.number(),
  cost_efficiency: z.number(),
})

export const AgentListResponseSchema = z.object({
  agents: z.array(AgentStatusSchema),
  total: z.number(),
  active: z.number(),
  inactive: z.number(),
})

export const AgentUpdateRequestSchema = z.object({
  name: z.string().optional(),
  retrieval: RetrievalConfigSchema.optional(),
  features: FeaturesConfigSchema.optional(),
  mcp_tools_allowlist: z.array(z.string()).optional(),
})

// ============================================================================
// Batch Search Models (from apps/api/routers/batch_search.py)
// ============================================================================

export const BatchSearchRequestSchema = z.object({
  queries: z.array(z.string()).min(1).max(50),
  max_results_per_query: z.number().min(1).max(100).default(10),
  deduplicate: z.boolean().default(true),
  taxonomy_filter: z.array(z.string()).default([]),
  parallel_execution: z.boolean().default(true),
})

export const BatchSearchResultSchema = z.object({
  query: z.string(),
  hits: z.array(SearchHitSchema),
  latency: z.number(),
  total_candidates: z.number(),
})

export const BatchSearchResponseSchema = z.object({
  results: z.array(BatchSearchResultSchema),
  total_latency: z.number(),
  total_queries: z.number(),
  total_unique_hits: z.number(),
  request_id: z.string(),
  parallel_execution: z.boolean(),
})

// ============================================================================
// Evaluation Models (from apps/evaluation/models.py)
// ============================================================================

export const EvaluationMetricsSchema = z.object({
  context_precision: z.number().min(0).max(1).optional(),
  context_recall: z.number().min(0).max(1).optional(),
  faithfulness: z.number().min(0).max(1).optional(),
  answer_relevancy: z.number().min(0).max(1).optional(),
  response_time: z.number().min(0).optional(),
  retrieval_score: z.number().min(0).max(1).optional(),
})

export const EvaluationRequestSchema = z.object({
  query: z.string(),
  response: z.string(),
  retrieved_contexts: z.array(z.string()),
  ground_truth: z.string().optional(),
  session_id: z.string().optional(),
  experiment_id: z.string().optional(),
  model_version: z.string().optional(),
})

export const EvaluationResultSchema = z.object({
  evaluation_id: z.string(),
  query: z.string(),
  metrics: EvaluationMetricsSchema,
  overall_score: z.number().min(0).max(1).default(0),
  quality_flags: z.array(z.string()).default([]),
  recommendations: z.array(z.string()).default([]),
  timestamp: z.string(),
  detailed_analysis: z.record(z.string(), z.any()).optional(),
})

export const QualityThresholdsSchema = z.object({
  faithfulness_min: z.number().min(0).max(1).default(0.85),
  context_precision_min: z.number().min(0).max(1).default(0.75),
  context_recall_min: z.number().min(0).max(1).default(0.70),
  answer_relevancy_min: z.number().min(0).max(1).default(0.80),
  response_time_max: z.number().min(0).default(5.0),
})

export const DatasetEntrySchema = z.object({
  query: z.string(),
  ground_truth_answer: z.string(),
  expected_contexts: z.array(z.string()),
  difficulty_level: z.enum(["easy", "medium", "hard"]).default("medium"),
  category: z.string().optional(),
  tags: z.array(z.string()).default([]),
})

// ============================================================================
// Legacy/Additional Models
// ============================================================================

export const DocumentUploadRequestSchema = z.object({
  file_name: z.string(),
  content_type: z.string(),
  taxonomy_id: z.string().optional(),
})

export const DocumentUploadResponseSchema = z.object({
  document_id: z.string(),
  status: z.string(),
  chunks_created: z.number().optional(),
})

export const HealthCheckResponseSchema = z.object({
  status: z.string(),
  database: z.string(),
  redis: z.string(),
  timestamp: z.string(),
})

export const PipelineExecuteRequestSchema = z.object({
  query: z.string(),
  config: z.record(z.string(), z.any()).optional(),
})

export const PipelineExecuteResponseSchema = z.object({
  result: z.any(),
  execution_time: z.number(),
  pipeline_id: z.string(),
})

export const AgentCreateRequestSchema = z.object({
  category: z.string(),
  config: z.record(z.string(), z.any()).optional(),
})

export const AgentResponseSchema = z.object({
  agent_id: z.string(),
  category: z.string(),
  status: z.string(),
})

export const EmbeddingGenerateRequestSchema = z.object({
  text: z.string(),
})

export const EmbeddingGenerateResponseSchema = z.object({
  embedding: z.array(z.number()),
  model: z.string(),
})

export const TaxonomyVersionSchema = z.object({
  version: z.string(),
  created_at: z.string(),
  is_active: z.boolean(),
})

// ============================================================================
// Type Exports
// ============================================================================

export type SourceMeta = z.infer<typeof SourceMetaSchema>
export type SearchHit = z.infer<typeof SearchHitSchema>
export type SearchRequest = z.infer<typeof SearchRequestSchema>
export type SearchResponse = z.infer<typeof SearchResponseSchema>
export type ClassificationResult = z.infer<typeof ClassificationResultSchema>
export type DocumentChunk = z.infer<typeof DocumentChunkSchema>
export type ProcessingStatus = z.infer<typeof ProcessingStatusSchema>
export type ErrorDetail = z.infer<typeof ErrorDetailSchema>
export type TaxonomyNode = z.infer<typeof TaxonomyNodeSchema>
export type ClassifyRequest = z.infer<typeof ClassifyRequestSchema>
export type ClassifyResponse = z.infer<typeof ClassifyResponseSchema>
export type FromCategoryRequest = z.infer<typeof FromCategoryRequestSchema>
export type RetrievalConfig = z.infer<typeof RetrievalConfigSchema>
export type FeaturesConfig = z.infer<typeof FeaturesConfigSchema>
export type AgentManifest = z.infer<typeof AgentManifestSchema>

export type AgentCreateResponse = z.infer<typeof AgentCreateResponseSchema>
export type AgentStatus = z.infer<typeof AgentStatusSchema>
export type AgentMetrics = z.infer<typeof AgentMetricsSchema>
export type AgentListResponse = z.infer<typeof AgentListResponseSchema>
export type AgentUpdateRequest = z.infer<typeof AgentUpdateRequestSchema>

export type BatchSearchRequest = z.infer<typeof BatchSearchRequestSchema>
export type BatchSearchResult = z.infer<typeof BatchSearchResultSchema>
export type BatchSearchResponse = z.infer<typeof BatchSearchResponseSchema>

export type EvaluationMetrics = z.infer<typeof EvaluationMetricsSchema>
export type EvaluationRequest = z.infer<typeof EvaluationRequestSchema>
export type EvaluationResult = z.infer<typeof EvaluationResultSchema>
export type QualityThresholds = z.infer<typeof QualityThresholdsSchema>
export type DatasetEntry = z.infer<typeof DatasetEntrySchema>

export type DocumentUploadRequest = z.infer<typeof DocumentUploadRequestSchema>
export type DocumentUploadResponse = z.infer<typeof DocumentUploadResponseSchema>
export type HealthCheckResponse = z.infer<typeof HealthCheckResponseSchema>
export type PipelineExecuteRequest = z.infer<typeof PipelineExecuteRequestSchema>
export type PipelineExecuteResponse = z.infer<typeof PipelineExecuteResponseSchema>
export type AgentCreateRequest = z.infer<typeof AgentCreateRequestSchema>
export type AgentResponse = z.infer<typeof AgentResponseSchema>
export type EmbeddingGenerateRequest = z.infer<typeof EmbeddingGenerateRequestSchema>
export type EmbeddingGenerateResponse = z.infer<typeof EmbeddingGenerateResponseSchema>
export type TaxonomyVersion = z.infer<typeof TaxonomyVersionSchema>
