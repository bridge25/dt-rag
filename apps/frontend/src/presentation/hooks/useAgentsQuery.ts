/**
 * useAgentsQuery Hook
 *
 * Presentation layer hook that uses the domain use case.
 * Integrates with React Query for caching and state management.
 *
 * @CODE:CLEAN-ARCHITECTURE-PRESENTATION
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Agent, AgentFilterParams, CreateAgentParams } from '../../domain/entities/Agent';
import {
  GetAgentsUseCase,
  GetAgentByIdUseCase,
  CreateAgentUseCase,
  type GetAgentsResult,
  type GetAgentByIdResult,
} from '../../domain/usecases/agent';
import { getAgentRepository } from '../../data/repositories/AgentRepositoryImpl';

// ============================================================================
// Query Keys
// ============================================================================

export const agentKeys = {
  all: ['agents'] as const,
  lists: () => [...agentKeys.all, 'list'] as const,
  list: (filters: AgentFilterParams) => [...agentKeys.lists(), filters] as const,
  details: () => [...agentKeys.all, 'detail'] as const,
  detail: (id: string) => [...agentKeys.details(), id] as const,
};

// ============================================================================
// Use Case Instances (Dependency Injection)
// ============================================================================

function getGetAgentsUseCase(): GetAgentsUseCase {
  return new GetAgentsUseCase(getAgentRepository());
}

function getGetAgentByIdUseCase(): GetAgentByIdUseCase {
  return new GetAgentByIdUseCase(getAgentRepository());
}

function getCreateAgentUseCase(): CreateAgentUseCase {
  return new CreateAgentUseCase(getAgentRepository());
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Hook for fetching agents list with computed metrics
 */
export function useAgentsQuery(params?: AgentFilterParams) {
  const useCase = getGetAgentsUseCase();

  return useQuery<GetAgentsResult, Error>({
    queryKey: agentKeys.list(params || {}),
    queryFn: () => useCase.execute(params),
    staleTime: 30000, // 30 seconds
    retry: 2,
  });
}

/**
 * Hook for fetching a single agent with metrics
 */
export function useAgentQuery(agentId: string | null) {
  const useCase = getGetAgentByIdUseCase();

  return useQuery<GetAgentByIdResult, Error>({
    queryKey: agentKeys.detail(agentId || ''),
    queryFn: () => useCase.execute(agentId!),
    enabled: !!agentId,
    staleTime: 30000,
    retry: 1,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Hook for creating a new agent
 */
export function useCreateAgent() {
  const queryClient = useQueryClient();
  const useCase = getCreateAgentUseCase();

  return useMutation<Agent, Error, CreateAgentParams>({
    mutationFn: (params) => useCase.execute(params),
    onSuccess: () => {
      // Invalidate agents list to refetch
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
  });
}

/**
 * Hook for updating an agent
 */
export function useUpdateAgent() {
  const queryClient = useQueryClient();
  const repository = getAgentRepository();

  return useMutation<Agent, Error, { id: string; params: Parameters<typeof repository.update>[1] }>({
    mutationFn: ({ id, params }) => repository.update(id, params),
    onSuccess: (agent) => {
      // Update cache for this specific agent
      queryClient.setQueryData(agentKeys.detail(agent.id), agent);
      // Invalidate list to refetch
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
  });
}

/**
 * Hook for deleting an agent
 */
export function useDeleteAgent() {
  const queryClient = useQueryClient();
  const repository = getAgentRepository();

  return useMutation<void, Error, string>({
    mutationFn: (id) => repository.delete(id),
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: agentKeys.detail(deletedId) });
      // Invalidate list to refetch
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
  });
}

// ============================================================================
// Selector Hooks (for derived state)
// ============================================================================

/**
 * Hook that returns only the agents array
 */
export function useAgentsList(params?: AgentFilterParams): {
  agents: Agent[];
  isLoading: boolean;
  error: Error | null;
} {
  const { data, isLoading, error } = useAgentsQuery(params);

  return {
    agents: data?.agents || [],
    isLoading,
    error: error || null,
  };
}

/**
 * Hook for getting performant agents only
 */
export function usePerformantAgents(): {
  agents: Agent[];
  count: number;
  isLoading: boolean;
} {
  const { data, isLoading } = useAgentsQuery();

  const performantAgents = data?.agents.filter(
    (agent) => agent.progress >= 70 && agent.stats.growth > 0
  ) || [];

  return {
    agents: performantAgents,
    count: data?.performantCount || 0,
    isLoading,
  };
}
