/**
 * Search Repository Interface
 *
 * Defines the contract for search data operations.
 * This interface follows the Repository Pattern for clean architecture.
 *
 * @CODE:CLEAN-ARCHITECTURE-DOMAIN
 */

import type { SearchResult, SearchParams } from '../entities/SearchResult';

/**
 * Search Repository Interface
 *
 * This interface defines all operations available for Search functionality.
 * The actual implementation is in the data layer.
 */
export interface ISearchRepository {
  /**
   * Execute a search query
   */
  search(params: SearchParams): Promise<SearchResult>;

  /**
   * Execute a batch search with multiple queries
   */
  batchSearch(queries: SearchParams[]): Promise<SearchResult[]>;

  /**
   * Get search suggestions based on partial query
   */
  getSuggestions(query: string, limit?: number): Promise<string[]>;

  /**
   * Get recent search history
   */
  getRecentSearches(limit?: number): Promise<RecentSearch[]>;

  /**
   * Save a search to history
   */
  saveToHistory(search: SearchParams): Promise<void>;

  /**
   * Clear search history
   */
  clearHistory(): Promise<void>;
}

/**
 * Recent search record
 */
export interface RecentSearch {
  readonly query: string;
  readonly timestamp: Date;
  readonly resultCount: number;
}

/**
 * Symbol for dependency injection
 */
export const ISearchRepository = Symbol('ISearchRepository');
