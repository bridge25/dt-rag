/**
 * Search Documents Use Case
 *
 * Business use case for searching documents with taxonomy filtering.
 *
 * @CODE:CLEAN-ARCHITECTURE-DOMAIN
 */

import type { SearchResult, SearchParams, SearchHit } from '../../entities/SearchResult';
import {
  filterHitsByScore,
  groupHitsByTaxonomy,
  getUniqueSources,
  calculateAverageScore,
} from '../../entities/SearchResult';
import type { ISearchRepository } from '../../repositories/ISearchRepository';

/**
 * Use Case Response with enriched data
 */
export interface SearchDocumentsResult {
  result: SearchResult;
  groupedByTaxonomy: Map<string, SearchHit[]>;
  uniqueSources: ReturnType<typeof getUniqueSources>;
  averageScore: number;
  highRelevanceCount: number;
}

/**
 * Search validation error
 */
export class SearchValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SearchValidationError';
  }
}

/**
 * Search Documents Use Case
 */
export class SearchDocumentsUseCase {
  constructor(private readonly searchRepository: ISearchRepository) {}

  /**
   * Execute the search use case
   */
  async execute(params: SearchParams): Promise<SearchDocumentsResult> {
    // Validate input
    this.validate(params);

    // Normalize query
    const normalizedParams: SearchParams = {
      ...params,
      query: params.query.trim(),
      maxResults: params.maxResults || 10,
      includeHighlights: params.includeHighlights ?? true,
      searchMode: params.searchMode || 'hybrid',
    };

    // Execute search
    const result = await this.searchRepository.search(normalizedParams);

    // Save to history (fire and forget)
    this.searchRepository.saveToHistory(normalizedParams).catch(() => {
      // Ignore history save errors
    });

    // Enrich result with computed data
    const highRelevanceHits = filterHitsByScore(result.hits, 0.8);
    const groupedByTaxonomy = groupHitsByTaxonomy(result.hits);
    const uniqueSources = getUniqueSources(result.hits);
    const averageScore = calculateAverageScore(result.hits);

    return {
      result,
      groupedByTaxonomy,
      uniqueSources,
      averageScore,
      highRelevanceCount: highRelevanceHits.length,
    };
  }

  /**
   * Validate search parameters
   */
  private validate(params: SearchParams): void {
    if (!params.query || params.query.trim().length === 0) {
      throw new SearchValidationError('Search query is required');
    }

    if (params.query.length > 1000) {
      throw new SearchValidationError('Search query must be less than 1000 characters');
    }

    if (params.maxResults !== undefined) {
      if (params.maxResults < 1) {
        throw new SearchValidationError('Max results must be at least 1');
      }
      if (params.maxResults > 100) {
        throw new SearchValidationError('Max results cannot exceed 100');
      }
    }

    if (params.minScore !== undefined) {
      if (params.minScore < 0 || params.minScore > 1) {
        throw new SearchValidationError('Min score must be between 0 and 1');
      }
    }
  }
}

/**
 * Factory function for creating the use case
 */
export function createSearchDocumentsUseCase(
  searchRepository: ISearchRepository
): SearchDocumentsUseCase {
  return new SearchDocumentsUseCase(searchRepository);
}
