// @TEST:AGENT-CARD-001-ERROR-001
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AgentCardErrorBoundary } from '../ErrorBoundary'

const ErrorThrowingComponent = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error')
  }
  return <div>Normal content</div>
}

describe('AgentCardErrorBoundary', () => {
  const originalConsoleError = console.error

  beforeEach(() => {
    console.error = vi.fn()
  })

  afterEach(() => {
    console.error = originalConsoleError
  })

  it('should render children when no error occurs', () => {
    render(
      <AgentCardErrorBoundary>
        <ErrorThrowingComponent shouldThrow={false} />
      </AgentCardErrorBoundary>
    )
    expect(screen.getByText('Normal content')).toBeInTheDocument()
  })

  it('should render fallback UI when error occurs', () => {
    render(
      <AgentCardErrorBoundary>
        <ErrorThrowingComponent shouldThrow={true} />
      </AgentCardErrorBoundary>
    )
    expect(screen.getByText('카드를 표시할 수 없습니다')).toBeInTheDocument()
    expect(screen.getByText(/페이지를 새로고침하거나/)).toBeInTheDocument()
  })

  it('should render custom fallback when provided', () => {
    const customFallback = <div>Custom error message</div>
    render(
      <AgentCardErrorBoundary fallback={customFallback}>
        <ErrorThrowingComponent shouldThrow={true} />
      </AgentCardErrorBoundary>
    )
    expect(screen.getByText('Custom error message')).toBeInTheDocument()
  })

  it('should call onError callback when error occurs', () => {
    const onError = vi.fn()
    render(
      <AgentCardErrorBoundary onError={onError}>
        <ErrorThrowingComponent shouldThrow={true} />
      </AgentCardErrorBoundary>
    )
    expect(onError).toHaveBeenCalledWith(
      expect.any(Error),
      expect.objectContaining({
        componentStack: expect.any(String),
      })
    )
  })

  it('should log error to console', () => {
    render(
      <AgentCardErrorBoundary>
        <ErrorThrowingComponent shouldThrow={true} />
      </AgentCardErrorBoundary>
    )
    expect(console.error).toHaveBeenCalled()
  })

  it('should have proper error boundary styling', () => {
    const { container } = render(
      <AgentCardErrorBoundary>
        <ErrorThrowingComponent shouldThrow={true} />
      </AgentCardErrorBoundary>
    )
    const errorCard = container.firstChild as HTMLElement
    expect(errorCard.className).toContain('border-red-400')
    expect(errorCard.className).toContain('w-[280px]')
  })
})
