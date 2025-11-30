/**
 * Get Agent By ID Use Case
 *
 * Business use case for retrieving a single agent with all details.
 *
 * @CODE:CLEAN-ARCHITECTURE-DOMAIN
 */

import type { Agent } from '../../entities/Agent';
import { calculateAgentHealthScore, calculateAgentRarity } from '../../entities/Agent';
import type { IAgentRepository, AgentMetrics, AgentCoverage } from '../../repositories/IAgentRepository';

/**
 * Use Case Response
 */
export interface GetAgentByIdResult {
  agent: Agent;
  metrics: AgentMetrics;
  coverage: AgentCoverage;
  healthScore: number;
  computedRarity: string;
}

/**
 * Agent Not Found Error
 */
export class AgentNotFoundError extends Error {
  constructor(agentId: string) {
    super(`Agent with ID ${agentId} not found`);
    this.name = 'AgentNotFoundError';
  }
}

/**
 * Get Agent By ID Use Case
 */
export class GetAgentByIdUseCase {
  constructor(private readonly agentRepository: IAgentRepository) {}

  /**
   * Execute the use case
   */
  async execute(agentId: string): Promise<GetAgentByIdResult> {
    // Get agent from repository
    const agent = await this.agentRepository.getById(agentId);

    if (!agent) {
      throw new AgentNotFoundError(agentId);
    }

    // Get additional data in parallel
    const [metrics, coverage] = await Promise.all([
      this.agentRepository.getMetrics(agentId),
      this.agentRepository.getCoverage(agentId),
    ]);

    // Compute business metrics
    const healthScore = calculateAgentHealthScore(agent);
    const computedRarity = agent.level
      ? calculateAgentRarity(agent.level)
      : 'common';

    return {
      agent,
      metrics,
      coverage,
      healthScore,
      computedRarity,
    };
  }
}

/**
 * Factory function for creating the use case
 */
export function createGetAgentByIdUseCase(
  agentRepository: IAgentRepository
): GetAgentByIdUseCase {
  return new GetAgentByIdUseCase(agentRepository);
}
