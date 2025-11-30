/**
 * Create Agent Use Case
 *
 * Business use case for creating a new agent with validation.
 *
 * @CODE:CLEAN-ARCHITECTURE-DOMAIN
 */

import type { Agent, CreateAgentParams } from '../../entities/Agent';
import type { IAgentRepository } from '../../repositories/IAgentRepository';

/**
 * Validation Error
 */
export class AgentValidationError extends Error {
  constructor(public readonly errors: string[]) {
    super(`Agent validation failed: ${errors.join(', ')}`);
    this.name = 'AgentValidationError';
  }
}

/**
 * Create Agent Use Case
 */
export class CreateAgentUseCase {
  constructor(private readonly agentRepository: IAgentRepository) {}

  /**
   * Execute the use case
   */
  async execute(params: CreateAgentParams): Promise<Agent> {
    // Validate input
    const validationErrors = this.validate(params);
    if (validationErrors.length > 0) {
      throw new AgentValidationError(validationErrors);
    }

    // Normalize input
    const normalizedParams: CreateAgentParams = {
      ...params,
      name: params.name.trim(),
      description: params.description?.trim(),
    };

    // Create agent via repository
    return this.agentRepository.create(normalizedParams);
  }

  /**
   * Validate agent creation parameters
   */
  private validate(params: CreateAgentParams): string[] {
    const errors: string[] = [];

    // Name validation
    if (!params.name || params.name.trim().length === 0) {
      errors.push('Agent name is required');
    } else if (params.name.length < 2) {
      errors.push('Agent name must be at least 2 characters');
    } else if (params.name.length > 100) {
      errors.push('Agent name must be less than 100 characters');
    }

    // Description validation (optional but if provided, must be valid)
    if (params.description && params.description.length > 500) {
      errors.push('Description must be less than 500 characters');
    }

    // Taxonomy scope validation
    if (params.taxonomyScope) {
      if (!Array.isArray(params.taxonomyScope)) {
        errors.push('Taxonomy scope must be an array');
      } else if (params.taxonomyScope.length > 10) {
        errors.push('Cannot assign more than 10 taxonomy scopes');
      }
    }

    return errors;
  }
}

/**
 * Factory function for creating the use case
 */
export function createCreateAgentUseCase(
  agentRepository: IAgentRepository
): CreateAgentUseCase {
  return new CreateAgentUseCase(agentRepository);
}
