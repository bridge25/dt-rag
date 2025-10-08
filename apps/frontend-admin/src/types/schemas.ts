import { z } from 'zod'

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

export const SearchResponseSchema = z.object({
  hits: z.array(SearchHitSchema),
  latency: z.number(),
  request_id: z.string(),
  total_candidates: z.number().optional(),
  sources_count: z.number().optional(),
  taxonomy_version: z.string().optional(),
  query_analysis: z.record(z.string(), z.any()).optional(),
})

export const TaxonomyNodeSchema = z.object({
  node_id: z.string(),
  label: z.string(),
  canonical_path: z.array(z.string()),
  version: z.string(),
  children: z.array(z.string()).optional(),
})

export const TaxonomyEdgeSchema = z.object({
  parent: z.string(),
  child: z.string(),
  version: z.string(),
})

export const TaxonomyTreeMetadataSchema = z.object({
  total_nodes: z.number(),
  timestamp: z.string(),
  error: z.string().optional(),
})

export const TaxonomyTreeSchema = z.object({
  nodes: z.array(TaxonomyNodeSchema),
  edges: z.array(TaxonomyEdgeSchema),
  version: z.string(),
  metadata: TaxonomyTreeMetadataSchema,
})

export const TaxonomyVersionSchema = z.object({
  version: z.string(),
  node_count: z.number(),
  created_at: z.union([z.string(), z.date()]).transform((val) =>
    typeof val === 'string' ? new Date(val) : val
  ),
  created_by: z.string(),
  change_summary: z.string(),
  parent_version: z.string().nullable(),
  depth: z.number(),
})

export const TaxonomyVersionsPaginationSchema = z.object({
  page: z.number(),
  limit: z.number(),
  total: z.number(),
  has_next: z.boolean(),
  has_previous: z.boolean(),
  next_page: z.number().optional(),
  previous_page: z.number().optional(),
})

export const TaxonomyVersionsResponseSchema = z.object({
  versions: z.array(TaxonomyVersionSchema),
  pagination: TaxonomyVersionsPaginationSchema,
})

export const TaxonomyStatisticsSchema = z.object({
  total_nodes: z.number(),
  leaf_nodes: z.number(),
  internal_nodes: z.number(),
  max_depth: z.number(),
  avg_depth: z.number(),
  categories_distribution: z.record(z.string(), z.number()),
})

export const ClassificationResultSchema = z.object({
  taxonomy_path: z.array(z.string()),
  confidence: z.number(),
  alternatives: z.array(z.object({
    path: z.array(z.string()),
    confidence: z.number(),
  })).optional(),
})

export const ClassifyResponseSchema = z.object({
  classifications: z.array(ClassificationResultSchema),
  request_id: z.string(),
  processing_time: z.number(),
  taxonomy_version: z.string().optional(),
})

export const ApiStatusComponentsSchema = z.record(z.string(), z.any())

export const ApiStatusSchema = z.object({
  status: z.string(),
  version: z.string(),
  components: ApiStatusComponentsSchema,
})

export const AnswerResultSchema = z.object({
  question: z.string(),
  answer: z.string(),
  sources: z.array(z.any()),
  source_count: z.number(),
  search_time: z.number(),
  generation_time: z.number(),
  total_time: z.number(),
  model: z.string(),
  language: z.string(),
  mode: z.string(),
})

export const HITLAlternativeNodeSchema = z.object({
  node_id: z.string(),
  canonical_path: z.array(z.string()),
})

export const HITLTaskSchema = z.object({
  task_id: z.string(),
  chunk_id: z.string(),
  text: z.string(),
  suggested_classification: z.array(z.string()),
  confidence: z.number(),
  alternatives: z.array(HITLAlternativeNodeSchema),
  created_at: z.string(),
  priority: z.string(),
})

export const VersionComparisonChangesSchema = z.object({
  added: z.array(TaxonomyNodeSchema),
  removed: z.array(TaxonomyNodeSchema),
  modified: z.array(z.object({
    node_id: z.string(),
    old: TaxonomyNodeSchema,
    new: TaxonomyNodeSchema,
  })),
})

export const VersionComparisonSummarySchema = z.object({
  added_count: z.number(),
  removed_count: z.number(),
  modified_count: z.number(),
  total_changes: z.number(),
})

export const VersionComparisonSchema = z.object({
  base_version: z.string(),
  target_version: z.string(),
  changes: VersionComparisonChangesSchema,
  summary: VersionComparisonSummarySchema,
})

export type SourceMeta = z.infer<typeof SourceMetaSchema>
export type SearchHit = z.infer<typeof SearchHitSchema>
export type SearchResponse = z.infer<typeof SearchResponseSchema>
export type TaxonomyNode = z.infer<typeof TaxonomyNodeSchema>
export type TaxonomyEdge = z.infer<typeof TaxonomyEdgeSchema>
export type TaxonomyTree = z.infer<typeof TaxonomyTreeSchema>
export type TaxonomyVersion = z.infer<typeof TaxonomyVersionSchema>
export type TaxonomyVersionsResponse = z.infer<typeof TaxonomyVersionsResponseSchema>
export type TaxonomyStatistics = z.infer<typeof TaxonomyStatisticsSchema>
export type ClassificationResult = z.infer<typeof ClassificationResultSchema>
export type ClassifyResponse = z.infer<typeof ClassifyResponseSchema>
export type ApiStatus = z.infer<typeof ApiStatusSchema>
export type AnswerResult = z.infer<typeof AnswerResultSchema>
export type HITLTask = z.infer<typeof HITLTaskSchema>
export type VersionComparison = z.infer<typeof VersionComparisonSchema>
