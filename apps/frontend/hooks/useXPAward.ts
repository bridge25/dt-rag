/**
 * Hook for awarding XP to agents with optimistic updates
 *
 * @CODE:FRONTEND-MIGRATION-002
 */
"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { awardXP, type AwardXPRequest, type AwardXPResponse } from "@/lib/api/xp"
import type { AgentCardData } from "@/lib/api/types"

interface UseXPAwardOptions {
  onSuccess?: (data: AwardXPResponse) => void
  onError?: (error: Error) => void
}

interface MutationContext {
  previousAgent?: AgentCardData
}

export function useXPAward(options?: UseXPAwardOptions) {
  const queryClient = useQueryClient()

  return useMutation<AwardXPResponse, Error, AwardXPRequest, MutationContext>({
    mutationFn: awardXP,
    onMutate: async (request): Promise<MutationContext> => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["agent", request.agentId] })

      // Snapshot the previous value
      const previousAgent = queryClient.getQueryData<AgentCardData>([
        "agent",
        request.agentId,
      ])

      // Optimistically update to the new value
      if (previousAgent) {
        queryClient.setQueryData<AgentCardData>(["agent", request.agentId], {
          ...previousAgent,
          current_xp: (previousAgent.current_xp ?? 0) + request.amount,
        })
      }

      return { previousAgent }
    },
    onError: (error, request, context) => {
      // Roll back on error
      if (context?.previousAgent) {
        queryClient.setQueryData(["agent", request.agentId], context.previousAgent)
      }
      options?.onError?.(error)
    },
    onSuccess: (data) => {
      options?.onSuccess?.(data)
    },
    onSettled: (_data, _error, request) => {
      // Always refetch after error or success
      queryClient.invalidateQueries({ queryKey: ["agent", request.agentId] })
      queryClient.invalidateQueries({ queryKey: ["agents"] })
    },
  })
}
