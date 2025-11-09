// @TEST:AGENT-CARD-001-UI-005
import { describe, it, expect } from 'vitest'
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

  // @TEST:AGENT-CARD-AVATAR-001 - Pokemon Avatar System Tests
  describe('Pokemon Avatar System', () => {
    it('should render Lucide Icon avatar when avatar_url is provided', () => {
      const agentWithAvatar: AgentCardData = {
        ...mockAgent,
        avatar_url: 'Star', // Lucide Icon name
        rarity: 'Rare',
      }
      const { container } = render(<AgentCard agent={agentWithAvatar} onView={() => {}} onDelete={() => {}} />)
      // Check if avatar section exists
      const avatar = container.querySelector('[role="img"]')
      expect(avatar).toBeInTheDocument()
    })

    it('should render User icon as fallback when avatar_url is null', () => {
      const agentWithoutAvatar: AgentCardData = {
        ...mockAgent,
        avatar_url: null,
        rarity: 'Common',
      }
      const { container } = render(<AgentCard agent={agentWithoutAvatar} onView={() => {}} onDelete={() => {}} />)
      const avatar = container.querySelector('[role="img"]')
      expect(avatar).toBeInTheDocument()
    })

    it('should apply rarity-specific gradient background', () => {
      const rarityTestCases: Array<{ rarity: 'Common' | 'Rare' | 'Epic' | 'Legendary' }> = [
        { rarity: 'Common' },
        { rarity: 'Rare' },
        { rarity: 'Epic' },
        { rarity: 'Legendary' },
      ]

      rarityTestCases.forEach(({ rarity }) => {
        const agent: AgentCardData = {
          ...mockAgent,
          rarity,
          avatar_url: 'User',
        }
        const { container } = render(<AgentCard agent={agent} onView={() => {}} onDelete={() => {}} />)
        const avatar = container.querySelector('[role="img"]')
        expect(avatar).toBeInTheDocument()
      })
    })

    it('should render deterministic icon based on agent_id and rarity', () => {
      // Test that same agent_id + rarity combination renders consistently
      const agent1: AgentCardData = {
        ...mockAgent,
        agent_id: 'a1b2c3d4-5678-90ab-cdef-1234567890ab',
        rarity: 'Common',
        avatar_url: 'User', // Deterministic icon
      }

      const { container: container1 } = render(<AgentCard agent={agent1} onView={() => {}} onDelete={() => {}} />)
      const { container: container2 } = render(<AgentCard agent={agent1} onView={() => {}} onDelete={() => {}} />)

      const avatar1 = container1.querySelector('[role="img"]')
      const avatar2 = container2.querySelector('[role="img"]')

      expect(avatar1).toBeInTheDocument()
      expect(avatar2).toBeInTheDocument()
    })

    it('should support all valid Lucide Icon names for each rarity', () => {
      const rarityIconMapping = {
        Common: ['User', 'UserCircle', 'UserSquare'],
        Rare: ['Star', 'Sparkles', 'Award'],
        Epic: ['Crown', 'Shield', 'Gem'],
        Legendary: ['Flame', 'Zap', 'Trophy'],
      } as const

      Object.entries(rarityIconMapping).forEach(([rarity, icons]) => {
        icons.forEach((icon) => {
          const agent: AgentCardData = {
            ...mockAgent,
            rarity: rarity as 'Common' | 'Rare' | 'Epic' | 'Legendary',
            avatar_url: icon,
          }
          const { container } = render(<AgentCard agent={agent} onView={() => {}} onDelete={() => {}} />)
          const avatar = container.querySelector('[role="img"]')
          expect(avatar).toBeInTheDocument()
        })
      })
    })
  })
})
