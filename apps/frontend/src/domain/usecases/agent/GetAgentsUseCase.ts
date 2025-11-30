/**
 * Get Agents Use Case
 *
 * Business use case for retrieving agents with optional filtering.
 * This use case orchestrates the repository and applies business rules.
 *
 * @CODE:CLEAN-ARCHITECTURE-DOMAIN
 */

import type { Agent, AgentFilterParams } from '../../entities/Agent';
import { calculateAgentHealthScore, isAgentPerformant } from '../../entities/Agent';
import type { IAgentRepository } from '../../repositories/IAgentRepository';

/**
 * Use Case Response
 */
export interface GetAgentsResult {
  agents: Agent[];
  total: number;
  performantCount: number;
  averageHealthScore: number;
}

/**
 * Get Agents Use Case
 *
 * Retrieves agents and enriches them with computed business metrics.
 */
export class GetAgentsUseCase {
  constructor(private readonly agentRepository: IAgentRepository) {}

  /**
   * Execute the use case
   */
  async execute(params?: AgentFilterParams): Promise<GetAgentsResult> {
    // Get agents from repository
    const agents = await this.agentRepository.getAll(params);

    // Apply business logic computations
    const performantAgents = agents.filter(isAgentPerformant);
    const healthScores = agents.map(calculateAgentHealthScore);
    const averageHealthScore =
      healthScores.length > 0
        ? healthScores.reduce((a, b) => a + b, 0) / healthScores.length
        : 0;

    return {
      agents,
      total: agents.length,
      performantCount: performantAgents.length,
      averageHealthScore: Math.round(averageHealthScore),
    };
  }
}

/**
 * Factory function for creating the use case
 */
export function createGetAgentsUseCase(
  agentRepository: IAgentRepository
): GetAgentsUseCase {
  return new GetAgentsUseCase(agentRepository);
}
