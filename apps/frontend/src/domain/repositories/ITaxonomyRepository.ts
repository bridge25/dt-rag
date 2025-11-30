/**
 * Taxonomy Repository Interface
 *
 * Defines the contract for taxonomy data operations.
 * This interface follows the Repository Pattern for clean architecture.
 *
 * @CODE:CLEAN-ARCHITECTURE-DOMAIN
 */

import type {
  TaxonomyNode,
  TaxonomyVersion,
  TaxonomyFilterParams,
} from '../entities/Taxonomy';

/**
 * Taxonomy Repository Interface
 *
 * This interface defines all operations available for Taxonomy entities.
 * The actual implementation is in the data layer.
 */
export interface ITaxonomyRepository {
  /**
   * Get taxonomy tree for a specific version
   */
  getTree(version: string): Promise<TaxonomyNode[]>;

  /**
   * Get a single taxonomy node by ID
   */
  getNode(nodeId: string, version?: string): Promise<TaxonomyNode | null>;

  /**
   * Get all taxonomy versions
   */
  getVersions(): Promise<TaxonomyVersion[]>;

  /**
   * Get the active taxonomy version
   */
  getActiveVersion(): Promise<TaxonomyVersion | null>;

  /**
   * Search taxonomy nodes
   */
  search(params: TaxonomyFilterParams): Promise<TaxonomyNode[]>;

  /**
   * Get children of a taxonomy node
   */
  getChildren(nodeId: string, version?: string): Promise<TaxonomyNode[]>;

  /**
   * Get ancestors of a taxonomy node
   */
  getAncestors(nodeId: string, version?: string): Promise<TaxonomyNode[]>;

  /**
   * Create a new taxonomy node
   */
  createNode(node: CreateTaxonomyNodeParams): Promise<TaxonomyNode>;

  /**
   * Update a taxonomy node
   */
  updateNode(nodeId: string, params: UpdateTaxonomyNodeParams): Promise<TaxonomyNode>;

  /**
   * Delete a taxonomy node
   */
  deleteNode(nodeId: string): Promise<void>;
}

/**
 * Parameters for creating a taxonomy node
 */
export interface CreateTaxonomyNodeParams {
  name: string;
  parentId: string | null;
  metadata?: Record<string, unknown>;
}

/**
 * Parameters for updating a taxonomy node
 */
export interface UpdateTaxonomyNodeParams {
  name?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Symbol for dependency injection
 */
export const ITaxonomyRepository = Symbol('ITaxonomyRepository');
