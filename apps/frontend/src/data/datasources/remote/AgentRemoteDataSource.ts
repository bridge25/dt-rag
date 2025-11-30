/**
 * Agent Remote Data Source
 *
 * Handles all HTTP communication with the Agent API endpoints.
 * Returns raw API response data (DTO).
 *
 * @CODE:CLEAN-ARCHITECTURE-DATA
 */

import { z } from 'zod';
import { getApiClient } from './api-client';

// ============================================================================
// API Response Schemas (DTOs)
// ============================================================================

export const AgentStatsDTO = z.object({
  users: z.number(),
  robos: z.number(),
  revenue: z.number(),
  growth: z.number(),
});

export const AgentDTO = z.object({
  agent_id: z.string(),
  name: z.string(),
  description: z.string().optional(),
  robotImage: z.string().optional(),
  status: z.enum(['active', 'idle', 'training', 'error']).default('active'),
  progress: z.number().default(0),
  stats: AgentStatsDTO.optional().default({ users: 0, robos: 0, revenue: 0, growth: 0 }),
  taxonomy_scope: z.array(z.string()).optional(),
  level: z.number().optional(),
  xp: z.number().optional(),
  rarity: z.enum(['common', 'rare', 'epic', 'legendary']).optional(),
  created_at: z.string().optional(),
  updated_at: z.string().optional(),
});

export const AgentsListResponseDTO = z.object({
  agents: z.array(AgentDTO),
  total: z.number().optional(),
});

export const AgentMetricsDTO = z.object({
  query_count: z.number(),
  success_rate: z.number(),
  avg_latency: z.number(),
  total_users: z.number(),
  daily_active_users: z.number(),
  error_rate: z.number(),
});

export const AgentCoverageDTO = z.object({
  coverage_percentage: z.number(),
  total_documents: z.number(),
  covered_documents: z.number(),
  taxonomy_nodes: z.number(),
  last_calculated: z.string(),
});

export const CreateAgentRequestDTO = z.object({
  name: z.string(),
  description: z.string().optional(),
  taxonomy_scope: z.array(z.string()).optional(),
  robot_image: z.string().optional(),
});

export const UpdateAgentRequestDTO = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
  status: z.enum(['active', 'idle', 'training', 'error']).optional(),
  taxonomy_scope: z.array(z.string()).optional(),
});

// Type exports
export type AgentDTOType = z.infer<typeof AgentDTO>;
export type AgentMetricsDTOType = z.infer<typeof AgentMetricsDTO>;
export type AgentCoverageDTOType = z.infer<typeof AgentCoverageDTO>;
export type CreateAgentRequestDTOType = z.infer<typeof CreateAgentRequestDTO>;
export type UpdateAgentRequestDTOType = z.infer<typeof UpdateAgentRequestDTO>;

// ============================================================================
// Data Source Class
// ============================================================================

/**
 * Agent Remote Data Source
 *
 * Responsible for API communication only - no business logic.
 */
export class AgentRemoteDataSource {
  /**
   * Get all agents
   */
  async getAll(params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<AgentDTOType[]> {
    const client = getApiClient();
    const response = await client.get('/agents/', { params });
    const validated = AgentsListResponseDTO.parse(response.data);
    return validated.agents;
  }

  /**
   * Get agent by ID
   */
  async getById(id: string): Promise<AgentDTOType | null> {
    try {
      const client = getApiClient();
      const response = await client.get(`/agents/${id}`);
      return AgentDTO.parse(response.data);
    } catch (error) {
      // Return null for 404 errors
      if ((error as { statusCode?: number }).statusCode === 404) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Create a new agent
   */
  async create(data: CreateAgentRequestDTOType): Promise<AgentDTOType> {
    const client = getApiClient();
    const validated = CreateAgentRequestDTO.parse(data);
    const response = await client.post('/agents/', validated);
    return AgentDTO.parse(response.data);
  }

  /**
   * Update an agent
   */
  async update(id: string, data: UpdateAgentRequestDTOType): Promise<AgentDTOType> {
    const client = getApiClient();
    const validated = UpdateAgentRequestDTO.parse(data);
    const response = await client.put(`/agents/${id}`, validated);
    return AgentDTO.parse(response.data);
  }

  /**
   * Delete an agent
   */
  async delete(id: string): Promise<void> {
    const client = getApiClient();
    await client.delete(`/agents/${id}`);
  }

  /**
   * Get agent metrics
   */
  async getMetrics(id: string): Promise<AgentMetricsDTOType> {
    const client = getApiClient();
    const response = await client.get(`/agents/${id}/metrics`);
    return AgentMetricsDTO.parse(response.data);
  }

  /**
   * Get agent coverage
   */
  async getCoverage(id: string): Promise<AgentCoverageDTOType> {
    const client = getApiClient();
    const response = await client.get(`/agents/${id}/coverage`);
    return AgentCoverageDTO.parse(response.data);
  }
}

/**
 * Singleton instance
 */
let instance: AgentRemoteDataSource | null = null;

export function getAgentRemoteDataSource(): AgentRemoteDataSource {
  if (!instance) {
    instance = new AgentRemoteDataSource();
  }
  return instance;
}
