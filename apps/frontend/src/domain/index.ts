/**
 * Domain Layer - Barrel Export
 *
 * The Domain Layer contains:
 * - Entities: Core business models (Agent, Taxonomy, SearchResult)
 * - Repositories: Interfaces for data access (IAgentRepository, etc.)
 * - Use Cases: Business logic orchestration (GetAgentsUseCase, etc.)
 *
 * @CODE:CLEAN-ARCHITECTURE-DOMAIN
 */

export * from './entities';
export * from './repositories';
export * from './usecases';
