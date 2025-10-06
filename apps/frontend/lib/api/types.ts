import { z } from "zod"

export const SearchRequestSchema = z.object({
  query: z.string(),
  top_k: z.number().optional(),
  filter: z.record(z.string(), z.any()).optional(),
  use_hybrid: z.boolean().optional(),
})

export const SearchResultSchema = z.object({
  chunk_id: z.string(),
  content: z.string(),
  score: z.number(),
  metadata: z.record(z.string(), z.any()),
})

export const SearchResponseSchema = z.object({
  results: z.array(SearchResultSchema),
  total: z.number(),
  query_id: z.string().optional(),
})

export const ClassifyRequestSchema = z.object({
  text: z.string(),
  categories: z.array(z.string()).optional(),
})

export const ClassifyResponseSchema = z.object({
  category: z.string(),
  confidence: z.number(),
  alternatives: z.array(z.object({
    category: z.string(),
    confidence: z.number(),
  })).optional(),
})

export const TaxonomyNodeSchema: z.ZodType<{
  id: string
  name: string
  description?: string
  parent_id: string | null
  children?: Array<{
    id: string
    name: string
    description?: string
    parent_id: string | null
    children?: any[]
  }>
}> = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().optional(),
  parent_id: z.string().nullable(),
  children: z.array(z.lazy(() => TaxonomyNodeSchema)).optional(),
})

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

export const EvaluationRequestSchema = z.object({
  query: z.string(),
  response: z.string(),
  ground_truth: z.string().optional(),
})

export const EvaluationResponseSchema = z.object({
  score: z.number(),
  metrics: z.record(z.string(), z.number()),
})

export const BatchSearchRequestSchema = z.object({
  queries: z.array(z.string()),
  max_results: z.number().optional(),
})

export const BatchSearchResponseSchema = z.object({
  results: z.array(SearchResponseSchema),
  total_time_ms: z.number(),
})

export const TaxonomyVersionSchema = z.object({
  version: z.string(),
  created_at: z.string(),
  is_active: z.boolean(),
})

export type SearchRequest = z.infer<typeof SearchRequestSchema>
export type SearchResponse = z.infer<typeof SearchResponseSchema>
export type ClassifyRequest = z.infer<typeof ClassifyRequestSchema>
export type ClassifyResponse = z.infer<typeof ClassifyResponseSchema>
export type TaxonomyNode = z.infer<typeof TaxonomyNodeSchema>
export type DocumentUploadRequest = z.infer<typeof DocumentUploadRequestSchema>
export type DocumentUploadResponse = z.infer<typeof DocumentUploadResponseSchema>
export type HealthCheckResponse = z.infer<typeof HealthCheckResponseSchema>
export type PipelineExecuteRequest = z.infer<typeof PipelineExecuteRequestSchema>
export type PipelineExecuteResponse = z.infer<typeof PipelineExecuteResponseSchema>
export type AgentCreateRequest = z.infer<typeof AgentCreateRequestSchema>
export type AgentResponse = z.infer<typeof AgentResponseSchema>
export type EmbeddingGenerateRequest = z.infer<typeof EmbeddingGenerateRequestSchema>
export type EmbeddingGenerateResponse = z.infer<typeof EmbeddingGenerateResponseSchema>
export type EvaluationRequest = z.infer<typeof EvaluationRequestSchema>
export type EvaluationResponse = z.infer<typeof EvaluationResponseSchema>
export type BatchSearchRequest = z.infer<typeof BatchSearchRequestSchema>
export type BatchSearchResponse = z.infer<typeof BatchSearchResponseSchema>
export type TaxonomyVersion = z.infer<typeof TaxonomyVersionSchema>
