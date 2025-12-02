/**
 * Agent Repository Interface
 *
 * Defines the contract for agent data operations.
 * This interface follows the Repository Pattern for clean architecture.
 *
 * @CODE:CLEAN-ARCHITECTURE-DOMAIN
 */

import type {
  Agent,
  AgentFilterParams,
  CreateAgentParams,
  UpdateAgentParams,
} from '../entities/Agent';

/**
 * Agent Repository Interface
 *
 * This interface defines all operations available for Agent entities.
 * The actual implementation is in the data layer.
 */
export interface IAgentRepository {
  /**
   * Get all agents with optional filtering
   */
  getAll(params?: AgentFilterParams): Promise<Agent[]>;

  /**
   * Get a single agent by ID
   */
  getById(id: string): Promise<Agent | null>;

  /**
   * Create a new agent
   */
  create(params: CreateAgentParams): Promise<Agent>;

  /**
   * Update an existing agent
   */
  update(id: string, params: UpdateAgentParams): Promise<Agent>;

  /**
   * Delete an agent by ID
   */
  delete(id: string): Promise<void>;

  /**
   * Get agent metrics
   */
  getMetrics(id: string): Promise<AgentMetrics>;

  /**
   * Calculate coverage for an agent
   */
  getCoverage(id: string): Promise<AgentCoverage>;
}

/**
 * Agent metrics data
 */
export interface AgentMetrics {
  readonly queryCount: number;
  readonly successRate: number;
  readonly avgLatency: number;
  readonly totalUsers: number;
  readonly dailyActiveUsers: number;
  readonly errorRate: number;
}

/**
 * Agent coverage data
 */
export interface AgentCoverage {
  readonly coveragePercentage: number;
  readonly totalDocuments: number;
  readonly coveredDocuments: number;
  readonly taxonomyNodes: number;
  readonly lastCalculated: Date;
}

/**
 * Symbol for dependency injection
 */
export const IAgentRepository = Symbol('IAgentRepository');
