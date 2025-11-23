/**
 * Test file
 *
 * @CODE:FRONTEND-001
 * @TEST:FRONTEND-001
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useXPAward } from './useXPAward'
import * as xpApi from '@/lib/api/xp'
import type { AgentCardData } from '@/lib/api/types'

vi.mock('@/lib/api/xp', () => ({
  awardXP: vi.fn(),
}))

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useXPAward', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should award XP successfully', async () => {
    const mockResponse = {
      agent_id: 'test-agent-id',
      current_xp: 110,
      new_level: 1,
      leveled_up: false,
    }

    vi.mocked(xpApi.awardXP).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useXPAward(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      agentId: 'test-agent-id',
      amount: 10,
      reason: 'chat',
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(xpApi.awardXP).toHaveBeenCalledWith(
      expect.objectContaining({
        agentId: 'test-agent-id',
        amount: 10,
        reason: 'chat',
      }),
      expect.anything()
    )
  })

  it('should call onSuccess callback', async () => {
    const mockResponse = {
      agent_id: 'test-agent-id',
      current_xp: 110,
      new_level: 1,
      leveled_up: false,
    }

    const onSuccess = vi.fn()

    vi.mocked(xpApi.awardXP).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useXPAward({ onSuccess }), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      agentId: 'test-agent-id',
      amount: 10,
      reason: 'chat',
    })

    await waitFor(() => expect(onSuccess).toHaveBeenCalledWith(mockResponse))
  })

  it('should call onError callback on failure', async () => {
    const error = new Error('Network error')
    const onError = vi.fn()

    vi.mocked(xpApi.awardXP).mockRejectedValue(error)

    const { result } = renderHook(() => useXPAward({ onError }), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      agentId: 'test-agent-id',
      amount: 10,
      reason: 'chat',
    })

    await waitFor(() => expect(onError).toHaveBeenCalledWith(error))
  })

  it('should handle optimistic updates', async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })

    const mockAgent: AgentCardData = {
      agent_id: 'test-agent-id',
      name: 'Test Agent',
      level: 1,
      current_xp: 100,
      next_level_xp: 500,
      rarity: 'Common',
      total_documents: 10,
      total_queries: 5,
      quality_score: 85,
      status: 'active',
      created_at: '2025-10-01T00:00:00Z',
    }

    queryClient.setQueryData(['agent', 'test-agent-id'], mockAgent)

    const mockResponse = {
      agent_id: 'test-agent-id',
      current_xp: 110,
      new_level: 1,
      leveled_up: false,
    }

    vi.mocked(xpApi.awardXP).mockResolvedValue(mockResponse)

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useXPAward(), { wrapper })

    result.current.mutate({
      agentId: 'test-agent-id',
      amount: 10,
      reason: 'chat',
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    const updatedAgent = queryClient.getQueryData<AgentCardData>(['agent', 'test-agent-id'])
    expect(updatedAgent?.current_xp).toBe(110)
  })
})
