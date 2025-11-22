/**
 * AgentCardErrorBoundary Component
 *
 * @CODE:AGENT-CARD-001
 */
import { Component, type ReactNode, type ErrorInfo } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class AgentCardErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('AgentCard Error:', error, errorInfo)
    this.props.onError?.(error, errorInfo)
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="w-[280px] p-4 bg-white rounded-lg border-2 border-red-400 shadow-md">
          <div className="text-center">
            <p className="text-sm font-semibold text-red-600 mb-2">
              카드를 표시할 수 없습니다
            </p>
            <p className="text-xs text-gray-600">
              페이지를 새로고침하거나 나중에 다시 시도해주세요.
            </p>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
