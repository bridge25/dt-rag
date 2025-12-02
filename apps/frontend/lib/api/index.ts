/**
 * API endpoints and functions
 *
 * @CODE:FRONTEND-001
 */

import { z } from "zod"
import { apiClient } from "./client"
import {
  SearchRequestSchema,
  SearchResponseSchema,
  ClassifyRequestSchema,
  ClassifyResponseSchema,
  TaxonomyNodeSchema,
  DocumentUploadResponseSchema,
  HealthCheckResponseSchema,
  EmbeddingGenerateRequestSchema,
  EmbeddingGenerateResponseSchema,
  EvaluationRequestSchema,
  EvaluationResultSchema,
  BatchSearchRequestSchema,
  BatchSearchResponseSchema,
  FromCategoryRequestSchema,
  AgentCreateResponseSchema,
  AgentListResponseSchema,
  AgentStatusSchema,
  AgentUpdateRequestSchema,
  AgentMetricsSchema,
  AgentStatsSchema,
  HITLTaskSchema,
  HITLReviewRequestSchema,
  HITLReviewResponseSchema,
  FeedbackRequestSchema,
  FeedbackResponseSchema,
  type SearchRequest,
  type SearchResponse,
  type ClassifyRequest,
  type ClassifyResponse,
  type TaxonomyNode,
  type DocumentUploadResponse,
  type HealthCheckResponse,
  type EmbeddingGenerateRequest,
  type EmbeddingGenerateResponse,
  type EvaluationRequest,
  type EvaluationResult,
  type BatchSearchRequest,
  type BatchSearchResponse,
  type FromCategoryRequest,
  type AgentCreateResponse,
  type AgentListResponse,
  type AgentStatus,
  type AgentUpdateRequest,
  type AgentMetrics,
  type HITLTask,
  type HITLReviewRequest,
  type HITLReviewResponse,
  type FeedbackRequest,
  type FeedbackResponse,
  type AgentStats,
} from "./types"

export async function search(request: SearchRequest): Promise<SearchResponse> {
  const validated = SearchRequestSchema.parse(request)
  const response = await apiClient.post("/search", validated)
  return SearchResponseSchema.parse(response.data)
}

export async function classify(request: ClassifyRequest): Promise<ClassifyResponse> {
  const validated = ClassifyRequestSchema.parse(request)
  const response = await apiClient.post("/classify", validated)
  return ClassifyResponseSchema.parse(response.data)
}

export async function getTaxonomyTree(version: string): Promise<TaxonomyNode[]> {
  const response = await apiClient.get(`/taxonomy/${version}/tree`)
  return z.array(TaxonomyNodeSchema).parse(response.data)
}

export async function uploadDocument(formData: FormData): Promise<DocumentUploadResponse> {
  const response = await apiClient.post("/ingestion/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  })
  return DocumentUploadResponseSchema.parse(response.data)
}

export async function getHealth(): Promise<HealthCheckResponse> {
  const response = await apiClient.get("/health")
  return HealthCheckResponseSchema.parse(response.data)
}

export async function getSystemHealth(): Promise<HealthCheckResponse> {
  const response = await apiClient.get("/monitoring/health")
  return HealthCheckResponseSchema.parse(response.data)
}

export async function generateEmbedding(request: EmbeddingGenerateRequest): Promise<EmbeddingGenerateResponse> {
  const validated = EmbeddingGenerateRequestSchema.parse(request)
  const response = await apiClient.post("/embeddings/generate", validated)
  return EmbeddingGenerateResponseSchema.parse(response.data)
}

export async function evaluateRagResponse(request: EvaluationRequest): Promise<EvaluationResult> {
  const validated = EvaluationRequestSchema.parse(request)
  const response = await apiClient.post("/evaluation/evaluate", validated)
  return EvaluationResultSchema.parse(response.data)
}

export async function batchSearch(request: BatchSearchRequest): Promise<BatchSearchResponse> {
  const validated = BatchSearchRequestSchema.parse(request)
  const response = await apiClient.post("/batch-search", validated)
  return BatchSearchResponseSchema.parse(response.data)
}

export async function createAgentFromCategory(request: FromCategoryRequest): Promise<AgentCreateResponse> {
  const validated = FromCategoryRequestSchema.parse(request)
  const response = await apiClient.post("/agents/from-category", validated)
  return AgentCreateResponseSchema.parse(response.data)
}

export async function listAgents(params?: { status?: string; limit?: number }): Promise<AgentListResponse> {
  const response = await apiClient.get("/agents", { params })
  return AgentListResponseSchema.parse(response.data)
}

export async function getAgent(agentId: string): Promise<AgentStatus> {
  const response = await apiClient.get(`/agents/${agentId}`)
  return AgentStatusSchema.parse(response.data)
}

export async function updateAgent(agentId: string, update: AgentUpdateRequest): Promise<AgentStatus> {
  const validated = AgentUpdateRequestSchema.parse(update)
  const response = await apiClient.put(`/agents/${agentId}`, validated)
  return AgentStatusSchema.parse(response.data)
}

export async function deleteAgent(agentId: string): Promise<{ message: string }> {
  const response = await apiClient.delete(`/agents/${agentId}`)
  return z.object({ message: z.string() }).parse(response.data)
}

export async function getAgentMetrics(agentId: string): Promise<AgentMetrics> {
  const response = await apiClient.get(`/agents/${agentId}/metrics`)
  return AgentMetricsSchema.parse(response.data)
}

export async function getHITLTasks(params?: { limit?: number; priority?: string }): Promise<HITLTask[]> {
  const response = await apiClient.get("/classify/hitl/tasks", { params })
  return z.array(HITLTaskSchema).parse(response.data)
}

export async function submitHITLReview(request: HITLReviewRequest): Promise<HITLReviewResponse> {
  const validated = HITLReviewRequestSchema.parse(request)
  const response = await apiClient.post("/classify/hitl/review", validated)
  return HITLReviewResponseSchema.parse(response.data)
}

// ============================================================================
// MENTOR MEMORY FEEDBACK FUNCTIONS
// ============================================================================

export async function submitFeedback(request: FeedbackRequest): Promise<FeedbackResponse> {
  const validated = FeedbackRequestSchema.parse(request)
  const response = await apiClient.post("/feedback", validated)
  return FeedbackResponseSchema.parse(response.data)
}

export async function getAgentStats(agentId: string): Promise<AgentStats> {
  const response = await apiClient.get(`/agents/${agentId}/stats`)
  return AgentStatsSchema.parse(response.data)
}

export * from "./types"
export * from "./agents"
export * from "./xp"
export * from "./history"
export * from "./research"
