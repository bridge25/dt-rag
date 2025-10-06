import { z } from "zod"
import { apiClient } from "./client"
import {
  SearchRequestSchema,
  SearchResponseSchema,
  ClassifyRequestSchema,
  ClassifyResponseSchema,
  TaxonomyNodeSchema,
  TaxonomyVersionSchema,
  DocumentUploadRequestSchema,
  DocumentUploadResponseSchema,
  HealthCheckResponseSchema,
  PipelineExecuteRequestSchema,
  PipelineExecuteResponseSchema,
  AgentCreateRequestSchema,
  AgentResponseSchema,
  EmbeddingGenerateRequestSchema,
  EmbeddingGenerateResponseSchema,
  EvaluationRequestSchema,
  EvaluationResponseSchema,
  BatchSearchRequestSchema,
  BatchSearchResponseSchema,
  type SearchRequest,
  type SearchResponse,
  type ClassifyRequest,
  type ClassifyResponse,
  type TaxonomyNode,
  type TaxonomyVersion,
  type DocumentUploadRequest,
  type DocumentUploadResponse,
  type HealthCheckResponse,
  type PipelineExecuteRequest,
  type PipelineExecuteResponse,
  type AgentCreateRequest,
  type AgentResponse,
  type EmbeddingGenerateRequest,
  type EmbeddingGenerateResponse,
  type EvaluationRequest,
  type EvaluationResponse,
  type BatchSearchRequest,
  type BatchSearchResponse,
} from "./types"

export async function search(params: SearchRequest): Promise<SearchResponse> {
  const validated = SearchRequestSchema.parse(params)
  const response = await apiClient.post("/search/", validated)
  return SearchResponseSchema.parse(response.data)
}

export async function classify(params: ClassifyRequest): Promise<ClassifyResponse> {
  const validated = ClassifyRequestSchema.parse(params)
  const response = await apiClient.post("/classify/", validated)
  return ClassifyResponseSchema.parse(response.data)
}

export async function getTaxonomyTree(version: string = "latest"): Promise<TaxonomyNode[]> {
  const response = await apiClient.get(`/taxonomy/${version}/tree`)
  return z.array(TaxonomyNodeSchema).parse(response.data)
}

export async function uploadDocument(params: DocumentUploadRequest, file: File): Promise<DocumentUploadResponse> {
  const validated = DocumentUploadRequestSchema.parse(params)
  const formData = new FormData()
  formData.append("file", file)
  formData.append("metadata", JSON.stringify(validated))

  const response = await apiClient.post("/ingestion/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  })
  return DocumentUploadResponseSchema.parse(response.data)
}

export async function getHealth(): Promise<HealthCheckResponse> {
  const response = await apiClient.get("/monitoring/health")
  return HealthCheckResponseSchema.parse(response.data)
}

export async function executePipeline(params: PipelineExecuteRequest): Promise<PipelineExecuteResponse> {
  const validated = PipelineExecuteRequestSchema.parse(params)
  const response = await apiClient.post("/api/v1/pipeline/execute", validated)
  return PipelineExecuteResponseSchema.parse(response.data)
}

export async function createAgentFromCategory(params: AgentCreateRequest): Promise<AgentResponse> {
  const validated = AgentCreateRequestSchema.parse(params)
  const response = await apiClient.post("/api/v1/agents/from-category", validated)
  return AgentResponseSchema.parse(response.data)
}

export async function activateAgent(agentId: string): Promise<AgentResponse> {
  const response = await apiClient.post(`/api/v1/agents/${agentId}/activate`)
  return AgentResponseSchema.parse(response.data)
}

export async function deactivateAgent(agentId: string): Promise<AgentResponse> {
  const response = await apiClient.post(`/api/v1/agents/${agentId}/deactivate`)
  return AgentResponseSchema.parse(response.data)
}

export async function deleteAgent(agentId: string): Promise<void> {
  await apiClient.delete(`/api/v1/agents/${agentId}`)
}

export async function generateEmbedding(params: EmbeddingGenerateRequest): Promise<EmbeddingGenerateResponse> {
  const validated = EmbeddingGenerateRequestSchema.parse(params)
  const response = await apiClient.post("/api/v1/embeddings/generate", validated)
  return EmbeddingGenerateResponseSchema.parse(response.data)
}

export async function evaluateResponse(params: EvaluationRequest): Promise<EvaluationResponse> {
  const validated = EvaluationRequestSchema.parse(params)
  const response = await apiClient.post("/api/v1/evaluation/evaluate", validated)
  return EvaluationResponseSchema.parse(response.data)
}

export async function batchSearch(params: BatchSearchRequest): Promise<BatchSearchResponse> {
  const validated = BatchSearchRequestSchema.parse(params)
  const response = await apiClient.post("/api/v1/batch/search", validated)
  return BatchSearchResponseSchema.parse(response.data)
}

export async function getTaxonomyVersions(): Promise<TaxonomyVersion[]> {
  const response = await apiClient.get("/api/v1/taxonomy/versions")
  return z.array(TaxonomyVersionSchema).parse(response.data)
}

export * from "./types"
