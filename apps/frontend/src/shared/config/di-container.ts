/**
 * Dependency Injection Container
 *
 * Central configuration for dependency injection.
 * Provides factory functions for creating instances with proper dependencies.
 *
 * @CODE:CLEAN-ARCHITECTURE-SHARED
 */

import type { IAgentRepository } from '../../domain/repositories/IAgentRepository';
import type { ITaxonomyRepository } from '../../domain/repositories/ITaxonomyRepository';
import type { ISearchRepository } from '../../domain/repositories/ISearchRepository';

import { GetAgentsUseCase, GetAgentByIdUseCase, CreateAgentUseCase } from '../../domain/usecases/agent';
import { SearchDocumentsUseCase } from '../../domain/usecases/search';
import { GetTaxonomyTreeUseCase } from '../../domain/usecases/taxonomy';

import { getAgentRepository, createMockAgentRepository } from '../../data/repositories/AgentRepositoryImpl';

// ============================================================================
// Container Configuration
// ============================================================================

interface DIContainerConfig {
  useMockData: boolean;
}

const defaultConfig: DIContainerConfig = {
  useMockData: process.env.NODE_ENV === 'development' &&
    process.env.NEXT_PUBLIC_USE_MOCK_DATA === 'true',
};

// ============================================================================
// Repository Providers
// ============================================================================

let agentRepository: IAgentRepository | null = null;
let taxonomyRepository: ITaxonomyRepository | null = null;
let searchRepository: ISearchRepository | null = null;

/**
 * Get Agent Repository
 */
export function provideAgentRepository(config = defaultConfig): IAgentRepository {
  if (!agentRepository) {
    agentRepository = config.useMockData
      ? createMockAgentRepository()
      : getAgentRepository();
  }
  return agentRepository;
}

/**
 * Reset repositories (for testing)
 */
export function resetRepositories(): void {
  agentRepository = null;
  taxonomyRepository = null;
  searchRepository = null;
}

// ============================================================================
// Use Case Providers
// ============================================================================

/**
 * Provide GetAgentsUseCase
 */
export function provideGetAgentsUseCase(): GetAgentsUseCase {
  return new GetAgentsUseCase(provideAgentRepository());
}

/**
 * Provide GetAgentByIdUseCase
 */
export function provideGetAgentByIdUseCase(): GetAgentByIdUseCase {
  return new GetAgentByIdUseCase(provideAgentRepository());
}

/**
 * Provide CreateAgentUseCase
 */
export function provideCreateAgentUseCase(): CreateAgentUseCase {
  return new CreateAgentUseCase(provideAgentRepository());
}

// ============================================================================
// Type-safe Container Access
// ============================================================================

/**
 * DI Container object for easier access
 */
export const DIContainer = {
  // Repositories
  agentRepository: () => provideAgentRepository(),

  // Use Cases - Agent
  getAgentsUseCase: () => provideGetAgentsUseCase(),
  getAgentByIdUseCase: () => provideGetAgentByIdUseCase(),
  createAgentUseCase: () => provideCreateAgentUseCase(),

  // Configuration
  config: defaultConfig,
  resetAll: resetRepositories,
};

export default DIContainer;
