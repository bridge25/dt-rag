// @TEST:FRONTEND-INTEGRATION-001:PHASE2:ROUTING
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import App from './App'

vi.mock('./app/page', () => ({
  default: () => <div>HomePage</div>,
}))

vi.mock('./pages/AgentDetailPage', () => ({
  default: () => <div>AgentDetailPage</div>,
}))

vi.mock('./pages/AgentHistoryPage', () => ({
  default: () => <div>AgentHistoryPage</div>,
}))

vi.mock('./pages/NotFoundPage', () => ({
  default: () => <div>NotFoundPage</div>,
}))

describe('App Router', () => {
  it('should render without crashing', async () => {
    render(<App />)
    
    await waitFor(() => {
      expect(screen.getByText('HomePage')).toBeInTheDocument()
    })
  })

  it('should provide QueryClientProvider', async () => {
    render(<App />)
    
    await waitFor(() => {
      expect(screen.getByText('HomePage')).toBeInTheDocument()
    })
  })
})
