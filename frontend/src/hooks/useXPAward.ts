// @CODE:FRONTEND-INTEGRATION-001:XP-HOOK
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { awardXP, type AwardXPRequest, type AwardXPResponse } from '@/lib/api/xp'
import type { AgentCardData } from '@/lib/api/types'

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
      await queryClient.cancelQueries({ queryKey: ['agent', request.agentId] })

      const previousAgent = queryClient.getQueryData<AgentCardData>(['agent', request.agentId])

      if (previousAgent) {
        queryClient.setQueryData<AgentCardData>(['agent', request.agentId], {
          ...previousAgent,
          current_xp: previousAgent.current_xp + request.amount,
        })
      }

      return { previousAgent }
    },
    onError: (error, request, context) => {
      if (context?.previousAgent) {
        queryClient.setQueryData(['agent', request.agentId], context.previousAgent)
      }
      options?.onError?.(error)
    },
    onSuccess: (data) => {
      options?.onSuccess?.(data)
    },
    onSettled: (_data, _error, request) => {
      queryClient.invalidateQueries({ queryKey: ['agent', request.agentId] })
      queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
  })
}
