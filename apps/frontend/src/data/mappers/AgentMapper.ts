/**
 * Agent Mapper
 *
 * Transforms data between API DTOs and Domain Entities.
 * This ensures clean separation between data layer and domain layer.
 *
 * @CODE:CLEAN-ARCHITECTURE-DATA
 */

import type { Agent, AgentStats, CreateAgentParams, UpdateAgentParams } from '../../domain/entities/Agent';
import type { AgentMetrics, AgentCoverage } from '../../domain/repositories/IAgentRepository';
import type {
  AgentDTOType,
  AgentMetricsDTOType,
  AgentCoverageDTOType,
  CreateAgentRequestDTOType,
  UpdateAgentRequestDTOType,
} from '../datasources/remote/AgentRemoteDataSource';

/**
 * Agent Mapper - Transforms between DTO and Domain Entity
 */
export class AgentMapper {
  /**
   * Map API DTO to Domain Entity
   */
  static toDomain(dto: AgentDTOType): Agent {
    return {
      id: dto.agent_id,
      name: dto.name,
      description: dto.description,
      robotImage: dto.robotImage || '/avatars/robots/robot-common-01.png',
      status: dto.status,
      progress: dto.progress,
      stats: this.mapStats(dto.stats),
      taxonomyScope: dto.taxonomy_scope,
      level: dto.level,
      xp: dto.xp,
      rarity: dto.rarity,
      createdAt: dto.created_at ? new Date(dto.created_at) : undefined,
      updatedAt: dto.updated_at ? new Date(dto.updated_at) : undefined,
    };
  }

  /**
   * Map Domain Entity to API DTO (for updates)
   */
  static toDTO(entity: Agent): AgentDTOType {
    return {
      agent_id: entity.id,
      name: entity.name,
      description: entity.description,
      robotImage: entity.robotImage,
      status: entity.status,
      progress: entity.progress,
      stats: {
        users: entity.stats.users,
        robos: entity.stats.robos,
        revenue: entity.stats.revenue,
        growth: entity.stats.growth,
      },
      taxonomy_scope: entity.taxonomyScope ? [...entity.taxonomyScope] : undefined,
      level: entity.level,
      xp: entity.xp,
      rarity: entity.rarity,
      created_at: entity.createdAt?.toISOString(),
      updated_at: entity.updatedAt?.toISOString(),
    };
  }

  /**
   * Map stats object
   */
  private static mapStats(stats?: AgentDTOType['stats']): AgentStats {
    return {
      users: stats?.users || 0,
      robos: stats?.robos || 0,
      revenue: stats?.revenue || 0,
      growth: stats?.growth || 0,
    };
  }

  /**
   * Map create params to DTO
   */
  static toCreateDTO(params: CreateAgentParams): CreateAgentRequestDTOType {
    return {
      name: params.name,
      description: params.description,
      taxonomy_scope: params.taxonomyScope,
      robot_image: params.robotImage,
    };
  }

  /**
   * Map update params to DTO
   */
  static toUpdateDTO(params: UpdateAgentParams): UpdateAgentRequestDTOType {
    return {
      name: params.name,
      description: params.description,
      status: params.status,
      taxonomy_scope: params.taxonomyScope,
    };
  }

  /**
   * Map metrics DTO to domain
   */
  static metricsTosDomain(dto: AgentMetricsDTOType): AgentMetrics {
    return {
      queryCount: dto.query_count,
      successRate: dto.success_rate,
      avgLatency: dto.avg_latency,
      totalUsers: dto.total_users,
      dailyActiveUsers: dto.daily_active_users,
      errorRate: dto.error_rate,
    };
  }

  /**
   * Map coverage DTO to domain
   */
  static coverageToDomain(dto: AgentCoverageDTOType): AgentCoverage {
    return {
      coveragePercentage: dto.coverage_percentage,
      totalDocuments: dto.total_documents,
      coveredDocuments: dto.covered_documents,
      taxonomyNodes: dto.taxonomy_nodes,
      lastCalculated: new Date(dto.last_calculated),
    };
  }
}
