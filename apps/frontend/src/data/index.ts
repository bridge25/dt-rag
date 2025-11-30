/**
 * Data Layer - Barrel Export
 *
 * The Data Layer contains:
 * - Data Sources: Remote API and Local Mock data providers
 * - Mappers: Transform DTOs to Domain Entities
 * - Repositories: Implement domain repository interfaces
 *
 * @CODE:CLEAN-ARCHITECTURE-DATA
 */

// Data Sources
export * from './datasources/remote/api-client';
export * from './datasources/remote/AgentRemoteDataSource';
export * from './datasources/local/MockAgentDataSource';

// Mappers
export * from './mappers/AgentMapper';

// Repositories
export * from './repositories/AgentRepositoryImpl';
