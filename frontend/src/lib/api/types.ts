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
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    children?: any[]
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    metadata?: Record<string, any>
    level: number
    document_count?: number
  }>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  metadata?: Record<string, any>
  level: number
  document_count?: number
}> = z.object({
  id: z.string(),
  name: z.string(),
  path: z.array(z.string()),
  parent_id: z.string().nullable(),
  children: z.array(z.lazy(() => TaxonomyNodeSchema)).optional(),
  metadata: z.record(z.string(), z.any()).optional(),
  level: z.number(),
  document_count: z.number().optional(),
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
// HITL Models (from apps/api/routers/classification_router.py)
// ============================================================================

export const HITLTaskSchema = z.object({
  task_id: z.string(),
  chunk_id: z.string(),
  text: z.string(),
  suggested_classification: z.array(z.string()),
  confidence: z.number(),
  alternatives: z.array(TaxonomyNodeSchema),
  created_at: z.string(),
  priority: z.enum(["low", "normal", "high", "urgent"]).default("normal"),
})

export const HITLReviewRequestSchema = z.object({
  chunk_id: z.string(),
  approved_path: z.array(z.string()),
  confidence_override: z.number().optional(),
  reviewer_notes: z.string().optional(),
})

export const HITLReviewResponseSchema = z.object({
  task_id: z.string(),
  status: z.string(),
  updated_classification: z.array(z.string()),
  reviewer_notes: z.string().optional(),
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

export type HITLTask = z.infer<typeof HITLTaskSchema>
export type HITLReviewRequest = z.infer<typeof HITLReviewRequestSchema>
export type HITLReviewResponse = z.infer<typeof HITLReviewResponseSchema>

// ============================================================================
// Agent Card Models (Frontend-specific)
// @CODE:POKEMON-IMAGE-COMPLETE-001-TYPES-001
// ============================================================================

export const RaritySchema = z.enum(['Common', 'Rare', 'Epic', 'Legendary'])
export type Rarity = z.infer<typeof RaritySchema>

export const AgentCardDataSchema = z.object({
  agent_id: z.string().uuid('Invalid agent ID format'),
  name: z.string().min(1, 'Name cannot be empty').max(100, 'Name too long'),
  level: z.number().int('Level must be an integer').min(1, 'Level must be at least 1').max(10, 'Level cannot exceed 10'),
  current_xp: z.number().int('XP must be an integer').min(0, 'XP cannot be negative'),
  next_level_xp: z.number().int('XP must be an integer').min(0, 'XP cannot be negative').nullable(),
  rarity: RaritySchema,
  total_documents: z.number().int('Document count must be an integer').min(0, 'Document count cannot be negative'),
  total_queries: z.number().int('Query count must be an integer').min(0, 'Query count cannot be negative'),
  quality_score: z.number().min(0, 'Quality score must be at least 0').max(100, 'Quality score cannot exceed 100'),
  status: z.string().min(1, 'Status cannot be empty'),
  created_at: z.string().datetime('Invalid datetime format'),
  last_used: z.string().datetime('Invalid datetime format').optional(),

  // Pokemon Avatar System Fields (SPEC-POKEMON-IMAGE-COMPLETE-001)
  avatar_url: z.string().max(500, 'Avatar URL too long').optional().nullable(),
  character_description: z.string().max(500, 'Character description too long').optional().nullable(),
}).refine(
  (data) => data.next_level_xp === null || data.next_level_xp > data.current_xp,
  {
    message: 'next_level_xp must be greater than current_xp',
    path: ['next_level_xp'],
  }
)

export type AgentCardData = z.infer<typeof AgentCardDataSchema>

// Helper function to get default avatar based on rarity and agent_id (deterministic)
export function getDefaultAvatarIcon(rarity: Rarity, agentId: string): string {
  // Deterministic icon selection based on agent_id hash
  const hash = agentId.split('-')[0] || '0'
  const index = (parseInt(hash, 16) % 3)  // 0, 1, or 2

  const RARITY_ICONS: Record<Rarity, string[]> = {
    'Common': ['User', 'UserCircle', 'UserSquare'],
    'Rare': ['Star', 'Sparkles', 'Award'],
    'Epic': ['Crown', 'Shield', 'Gem'],
    'Legendary': ['Flame', 'Zap', 'Trophy']
  }

  return RARITY_ICONS[rarity][index]
}

// ============================================================================
// @CODE:FRONTEND-INTEGRATION-001:TYPES-UPDATE
// Additional Types for Backend Integration
// ============================================================================

export type AgentCardResponse = AgentCardData

export const CoverageResponseSchema = z.object({
  agent_id: z.string(),
  coverage_percentage: z.number(),
  total_documents: z.number(),
  covered_documents: z.number(),
  taxonomy_depth: z.number(),
})

export type CoverageResponse = z.infer<typeof CoverageResponseSchema>

export const AwardXPRequestSchema = z.object({
  agentId: z.string(),
  amount: z.number().positive(),
  reason: z.enum(['chat', 'positive_feedback', 'ragas_bonus']),
})

export type AwardXPRequestType = z.infer<typeof AwardXPRequestSchema>

export const AwardXPResponseSchema = z.object({
  agent_id: z.string(),
  current_xp: z.number(),
  new_level: z.number(),
  leveled_up: z.boolean(),
})

export type AwardXPResponseType = z.infer<typeof AwardXPResponseSchema>

export const CoverageHistoryItemSchema = z.object({
  date: z.string(),
  coverage: z.number(),
  xp: z.number(),
})

export type CoverageHistoryItemType = z.infer<typeof CoverageHistoryItemSchema>

export const CoverageHistoryResponseSchema = z.object({
  agent_id: z.string(),
  history: z.array(CoverageHistoryItemSchema),
  interval: z.enum(['daily', 'weekly', 'monthly']),
})

export type CoverageHistoryResponseType = z.infer<typeof CoverageHistoryResponseSchema>
