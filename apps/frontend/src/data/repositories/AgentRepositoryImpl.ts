/**
 * Agent Repository Implementation
 *
 * Implements the IAgentRepository interface from domain layer.
 * Coordinates between data sources and applies data transformations.
 *
 * @CODE:CLEAN-ARCHITECTURE-DATA
 */

import type {
  Agent,
  AgentFilterParams,
  CreateAgentParams,
  UpdateAgentParams,
} from '../../domain/entities/Agent';
import type {
  IAgentRepository,
  AgentMetrics,
  AgentCoverage,
} from '../../domain/repositories/IAgentRepository';
import { AgentMapper } from '../mappers/AgentMapper';
import { AgentRemoteDataSource, getAgentRemoteDataSource } from '../datasources/remote/AgentRemoteDataSource';
import { MockAgentDataSource, getMockAgentDataSource } from '../datasources/local/MockAgentDataSource';

/**
 * Agent Repository Implementation
 *
 * Uses remote data source by default, falls back to mock data on error.
 */
export class AgentRepositoryImpl implements IAgentRepository {
  constructor(
    private readonly remoteDataSource: AgentRemoteDataSource,
    private readonly mockDataSource: MockAgentDataSource,
    private readonly useMockData: boolean = false
  ) {}

  /**
   * Get the appropriate data source
   */
  private getDataSource() {
    return this.useMockData ? this.mockDataSource : this.remoteDataSource;
  }

  /**
   * Execute with fallback to mock data on error
   */
  private async withFallback<T>(
    remoteFn: () => Promise<T>,
    mockFn: () => Promise<T>
  ): Promise<T> {
    if (this.useMockData) {
      return mockFn();
    }

    try {
      return await remoteFn();
    } catch (error) {
      console.warn('Remote API failed, falling back to mock data:', error);
      return mockFn();
    }
  }

  /**
   * Get all agents with optional filtering
   */
  async getAll(params?: AgentFilterParams): Promise<Agent[]> {
    const dtos = await this.withFallback(
      () => this.remoteDataSource.getAll({
        status: params?.status,
        limit: params?.limit,
        offset: params?.offset,
      }),
      () => this.mockDataSource.getAll({
        status: params?.status,
        limit: params?.limit,
        offset: params?.offset,
      })
    );

    // Transform DTOs to domain entities
    let agents = dtos.map(AgentMapper.toDomain);

    // Apply domain-level filtering
    if (params?.minLevel !== undefined) {
      agents = agents.filter((a) => (a.level || 0) >= params.minLevel!);
    }
    if (params?.maxLevel !== undefined) {
      agents = agents.filter((a) => (a.level || 0) <= params.maxLevel!);
    }
    if (params?.rarity) {
      agents = agents.filter((a) => a.rarity === params.rarity);
    }

    return agents;
  }

  /**
   * Get a single agent by ID
   */
  async getById(id: string): Promise<Agent | null> {
    const dto = await this.withFallback(
      () => this.remoteDataSource.getById(id),
      () => this.mockDataSource.getById(id)
    );

    return dto ? AgentMapper.toDomain(dto) : null;
  }

  /**
   * Create a new agent
   */
  async create(params: CreateAgentParams): Promise<Agent> {
    const createDto = AgentMapper.toCreateDTO(params);

    const dto = await this.withFallback(
      () => this.remoteDataSource.create(createDto),
      () => this.mockDataSource.create(createDto)
    );

    return AgentMapper.toDomain(dto);
  }

  /**
   * Update an existing agent
   */
  async update(id: string, params: UpdateAgentParams): Promise<Agent> {
    const updateDto = AgentMapper.toUpdateDTO(params);

    const dto = await this.withFallback(
      () => this.remoteDataSource.update(id, updateDto),
      () => this.mockDataSource.update(id, updateDto)
    );

    return AgentMapper.toDomain(dto);
  }

  /**
   * Delete an agent by ID
   */
  async delete(id: string): Promise<void> {
    await this.withFallback(
      () => this.remoteDataSource.delete(id),
      () => this.mockDataSource.delete(id)
    );
  }

  /**
   * Get agent metrics
   */
  async getMetrics(id: string): Promise<AgentMetrics> {
    const dto = await this.withFallback(
      () => this.remoteDataSource.getMetrics(id),
      () => this.mockDataSource.getMetrics(id)
    );

    return AgentMapper.metricsTosDomain(dto);
  }

  /**
   * Calculate coverage for an agent
   */
  async getCoverage(id: string): Promise<AgentCoverage> {
    const dto = await this.withFallback(
      () => this.remoteDataSource.getCoverage(id),
      () => this.mockDataSource.getCoverage(id)
    );

    return AgentMapper.coverageToDomain(dto);
  }
}

// ============================================================================
// Factory Functions
// ============================================================================

/**
 * Create agent repository with real API
 */
export function createAgentRepository(): IAgentRepository {
  return new AgentRepositoryImpl(
    getAgentRemoteDataSource(),
    getMockAgentDataSource(),
    false
  );
}

/**
 * Create agent repository with mock data only
 */
export function createMockAgentRepository(): IAgentRepository {
  return new AgentRepositoryImpl(
    getAgentRemoteDataSource(),
    getMockAgentDataSource(),
    true
  );
}

/**
 * Singleton instance
 */
let repositoryInstance: IAgentRepository | null = null;

export function getAgentRepository(): IAgentRepository {
  if (!repositoryInstance) {
    // Use mock data in development if API is not available
    const useMock = process.env.NODE_ENV === 'development' &&
      process.env.NEXT_PUBLIC_USE_MOCK_DATA === 'true';

    repositoryInstance = new AgentRepositoryImpl(
      getAgentRemoteDataSource(),
      getMockAgentDataSource(),
      useMock
    );
  }
  return repositoryInstance;
}
