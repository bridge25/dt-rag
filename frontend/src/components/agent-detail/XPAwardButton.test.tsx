// @TEST:FRONTEND-INTEGRATION-001:PHASE3:XP-BUTTON
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider, type UseMutationResult } from '@tanstack/react-query'
import { XPAwardButton } from './XPAwardButton'
import * as useXPAwardModule from '@/hooks/useXPAward'
import type { AwardXPRequest, AwardXPResponse } from '@/lib/api/xp'

vi.mock('@/hooks/useXPAward')

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

type MockXPAwardResult = Partial<UseMutationResult<AwardXPResponse, Error, AwardXPRequest, unknown>>

describe('XPAwardButton', () => {
  const mockMutate = vi.fn()
  const mockUseXPAward: MockXPAwardResult = {
    mutate: mockMutate,
    isPending: false,
    isSuccess: false,
    isError: false,
    data: undefined,
    error: null,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useXPAwardModule.useXPAward).mockReturnValue(mockUseXPAward as UseMutationResult<AwardXPResponse, Error, AwardXPRequest, unknown>)
  })

  it('should render all XP award buttons', () => {
    render(<XPAwardButton agentId="test-agent-id" />, { wrapper: createWrapper() })

    expect(screen.getByText('대화 완료 (+10 XP)')).toBeInTheDocument()
    expect(screen.getByText('긍정 피드백 (+50 XP)')).toBeInTheDocument()
    expect(screen.getByText('RAGAS 보너스 (+100 XP)')).toBeInTheDocument()
  })

  it('should call mutate with correct parameters for chat', async () => {
    const user = userEvent.setup()
    render(<XPAwardButton agentId="test-agent-id" />, { wrapper: createWrapper() })

    const chatButton = screen.getByText('대화 완료 (+10 XP)')
    await user.click(chatButton)

    expect(mockMutate).toHaveBeenCalledWith({
      agentId: 'test-agent-id',
      amount: 10,
      reason: 'chat',
    })
  })

  it('should call mutate with correct parameters for positive feedback', async () => {
    const user = userEvent.setup()
    render(<XPAwardButton agentId="test-agent-id" />, { wrapper: createWrapper() })

    const feedbackButton = screen.getByText('긍정 피드백 (+50 XP)')
    await user.click(feedbackButton)

    expect(mockMutate).toHaveBeenCalledWith({
      agentId: 'test-agent-id',
      amount: 50,
      reason: 'positive_feedback',
    })
  })

  it('should call mutate with correct parameters for RAGAS bonus', async () => {
    const user = userEvent.setup()
    render(<XPAwardButton agentId="test-agent-id" />, { wrapper: createWrapper() })

    const ragasButton = screen.getByText('RAGAS 보너스 (+100 XP)')
    await user.click(ragasButton)

    expect(mockMutate).toHaveBeenCalledWith({
      agentId: 'test-agent-id',
      amount: 100,
      reason: 'ragas_bonus',
    })
  })

  it('should show loading state when pending', () => {
    vi.mocked(useXPAwardModule.useXPAward).mockReturnValue({
      ...mockUseXPAward,
      isPending: true,
    } as UseMutationResult<AwardXPResponse, Error, AwardXPRequest, unknown>)

    render(<XPAwardButton agentId="test-agent-id" />, { wrapper: createWrapper() })

    const buttons = screen.getAllByRole('button')
    buttons.forEach((button) => {
      expect(button).toBeDisabled()
      expect(button).toHaveTextContent('Processing...')
    })
  })

  it('should call onLevelUp callback when leveled up', () => {
    const onLevelUp = vi.fn()
    let capturedOnSuccess: ((data: AwardXPResponse) => void) | undefined

    vi.mocked(useXPAwardModule.useXPAward).mockImplementation((options) => {
      capturedOnSuccess = options?.onSuccess
      return mockUseXPAward as UseMutationResult<AwardXPResponse, Error, AwardXPRequest, unknown>
    })

    render(<XPAwardButton agentId="test-agent-id" onLevelUp={onLevelUp} />, {
      wrapper: createWrapper(),
    })

    expect(capturedOnSuccess).toBeDefined()

    capturedOnSuccess?.({
      agent_id: 'test-agent-id',
      current_xp: 500,
      new_level: 2,
      leveled_up: true,
    })

    expect(onLevelUp).toHaveBeenCalledWith(1, 2)
  })

  it('should not call onLevelUp when not leveled up', () => {
    const onLevelUp = vi.fn()
    let capturedOnSuccess: ((data: AwardXPResponse) => void) | undefined

    vi.mocked(useXPAwardModule.useXPAward).mockImplementation((options) => {
      capturedOnSuccess = options?.onSuccess
      return mockUseXPAward as UseMutationResult<AwardXPResponse, Error, AwardXPRequest, unknown>
    })

    render(<XPAwardButton agentId="test-agent-id" onLevelUp={onLevelUp} />, {
      wrapper: createWrapper(),
    })

    capturedOnSuccess?.({
      agent_id: 'test-agent-id',
      current_xp: 110,
      new_level: 1,
      leveled_up: false,
    })

    expect(onLevelUp).not.toHaveBeenCalled()
  })
})
