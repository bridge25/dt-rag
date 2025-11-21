/**
 * AgentCard Component Tests
 * @TEST:FRONTEND-MIGRATION-001
 */

import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { AgentCard } from "../AgentCard"
import type { AgentCardData } from "../types"

const mockAgent: AgentCardData = {
  agent_id: "test-agent-1",
  name: "Test Agent",
  level: 5,
  current_xp: 1200,
  next_level_xp: 2000,
  rarity: "Rare",
  total_documents: 42,
  total_queries: 150,
  quality_score: 85,
  avatar_url: null,
}

describe("AgentCard", () => {
  const defaultProps = {
    agent: mockAgent,
    onView: vi.fn(),
    onDelete: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("renders agent name", () => {
    render(<AgentCard {...defaultProps} />)
    expect(screen.getByText("Test Agent")).toBeInTheDocument()
  })

  it("renders agent level", () => {
    render(<AgentCard {...defaultProps} />)
    expect(screen.getByText("Level 5")).toBeInTheDocument()
  })

  it("renders rarity badge", () => {
    render(<AgentCard {...defaultProps} />)
    expect(screen.getByText("Rare")).toBeInTheDocument()
  })

  it("renders XP progress", () => {
    render(<AgentCard {...defaultProps} />)
    expect(screen.getByText("1200 / 2000 XP")).toBeInTheDocument()
  })

  it("renders stats", () => {
    render(<AgentCard {...defaultProps} />)
    expect(screen.getByText("42")).toBeInTheDocument()
    expect(screen.getByText("150")).toBeInTheDocument()
    expect(screen.getByText("85")).toBeInTheDocument()
  })

  it("calls onView when View button clicked", () => {
    render(<AgentCard {...defaultProps} />)
    fireEvent.click(screen.getByText("View"))
    expect(defaultProps.onView).toHaveBeenCalledTimes(1)
  })

  it("calls onDelete when Delete button clicked", () => {
    render(<AgentCard {...defaultProps} />)
    fireEvent.click(screen.getByText("Delete"))
    expect(defaultProps.onDelete).toHaveBeenCalledTimes(1)
  })

  it("has correct aria-label", () => {
    render(<AgentCard {...defaultProps} />)
    expect(
      screen.getByRole("article", {
        name: /Test Agent - Level 5 Rare agent/i,
      })
    ).toBeInTheDocument()
  })

  it("applies border color based on rarity", () => {
    const { container } = render(<AgentCard {...defaultProps} />)
    const article = container.querySelector("article")
    expect(article).toHaveClass("border-blue-400")
  })

  it("handles Legendary rarity", () => {
    const legendaryAgent = { ...mockAgent, rarity: "Legendary" as const }
    const { container } = render(
      <AgentCard {...defaultProps} agent={legendaryAgent} />
    )
    const article = container.querySelector("article")
    expect(article).toHaveClass("border-amber-500")
  })
})
