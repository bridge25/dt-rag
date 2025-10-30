// @TEST:AGENT-CARD-001-UI-005
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AgentCard } from '../AgentCard'
import type { AgentCardData } from '@/lib/api/types'

const mockAgent: AgentCardData = {
  agent_id: 'agent-1',
  name: 'Test Agent',
  level: 5,
  current_xp: 1200,
  next_level_xp: 2000,
  rarity: 'Rare',
  total_documents: 150,
  total_queries: 500,
  quality_score: 85,
  status: 'active',
  created_at: '2025-01-01T00:00:00Z',
}

describe('AgentCard', () => {
  it('should render agent name', () => {
    render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)
    expect(screen.getByText('Test Agent')).toBeInTheDocument()
  })

  it('should render level', () => {
    render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)
    expect(screen.getByText(/Level 5/i)).toBeInTheDocument()
  })

  it('should render rarity badge', () => {
    render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)
    expect(screen.getByText('Rare')).toBeInTheDocument()
  })

  it('should render stats', () => {
    render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)
    expect(screen.getByText('150')).toBeInTheDocument() // documents
    expect(screen.getByText('500')).toBeInTheDocument() // queries
    expect(screen.getByText('85')).toBeInTheDocument() // quality score
  })

  it('should render progress bar', () => {
    render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)
    const progressBar = screen.getByRole('progressbar')
    expect(progressBar).toHaveAttribute('aria-valuenow', '1200')
    expect(progressBar).toHaveAttribute('aria-valuemax', '2000')
  })

  it('should render action buttons', () => {
    render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)
    expect(screen.getByText('View')).toBeInTheDocument()
    expect(screen.getByText('Delete')).toBeInTheDocument()
  })

  it('should have rarity-based border styling', () => {
    const { container } = render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)
    const card = container.firstChild as HTMLElement
    expect(card.className).toContain('border')
  })
})
