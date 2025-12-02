/**
 * SearchResult Domain Entity
 *
 * Core business entity representing search results.
 * This entity is framework-agnostic and contains only business logic.
 *
 * @CODE:CLEAN-ARCHITECTURE-DOMAIN
 */

/**
 * Source metadata for a search hit
 */
export interface SourceMeta {
  readonly url: string;
  readonly title: string;
  readonly date: string;
  readonly author?: string;
  readonly contentType?: string;
  readonly language?: string;
}

/**
 * Individual search hit entity
 */
export interface SearchHit {
  readonly chunkId: string;
  readonly score: number;
  readonly text: string;
  readonly source: SourceMeta;
  readonly taxonomyPath: readonly string[];
  readonly highlights?: readonly string[];
  readonly metadata?: Record<string, unknown>;
}

/**
 * Search response entity
 */
export interface SearchResult {
  readonly hits: readonly SearchHit[];
  readonly latency: number;
  readonly requestId: string;
  readonly totalCandidates?: number;
  readonly sourcesCount?: number;
  readonly taxonomyVersion?: string;
  readonly queryAnalysis?: Record<string, unknown>;
}

/**
 * Search request parameters
 */
export interface SearchParams {
  query: string;
  maxResults?: number;
  taxonomyFilter?: string[][];
  minScore?: number;
  includeHighlights?: boolean;
  searchMode?: 'hybrid' | 'bm25' | 'vector';
}

/**
 * Domain logic: Get relevance category from score
 */
export function getRelevanceCategory(score: number): 'high' | 'medium' | 'low' {
  if (score >= 0.8) return 'high';
  if (score >= 0.5) return 'medium';
  return 'low';
}

/**
 * Domain logic: Filter hits by minimum score
 */
export function filterHitsByScore(
  hits: readonly SearchHit[],
  minScore: number
): SearchHit[] {
  return hits.filter(hit => hit.score >= minScore);
}

/**
 * Domain logic: Group hits by taxonomy path
 */
export function groupHitsByTaxonomy(
  hits: readonly SearchHit[]
): Map<string, SearchHit[]> {
  const grouped = new Map<string, SearchHit[]>();

  for (const hit of hits) {
    const pathKey = hit.taxonomyPath.join(' > ');
    const existing = grouped.get(pathKey) || [];
    grouped.set(pathKey, [...existing, hit]);
  }

  return grouped;
}

/**
 * Domain logic: Get unique sources from hits
 */
export function getUniqueSources(hits: readonly SearchHit[]): SourceMeta[] {
  const sourceMap = new Map<string, SourceMeta>();

  for (const hit of hits) {
    if (!sourceMap.has(hit.source.url)) {
      sourceMap.set(hit.source.url, hit.source);
    }
  }

  return Array.from(sourceMap.values());
}

/**
 * Domain logic: Calculate average score
 */
export function calculateAverageScore(hits: readonly SearchHit[]): number {
  if (hits.length === 0) return 0;
  const sum = hits.reduce((acc, hit) => acc + hit.score, 0);
  return sum / hits.length;
}

/**
 * Domain logic: Check if search was successful
 */
export function isSearchSuccessful(result: SearchResult): boolean {
  return result.hits.length > 0 && result.latency < 5000;
}
