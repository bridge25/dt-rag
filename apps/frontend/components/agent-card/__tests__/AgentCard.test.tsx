/**
 * AgentCard Component Tests - Ethereal Glass Design
 * @TEST:FRONTEND-REDESIGN-001
 */

import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { AgentCard } from "../AgentCard"
import type { AgentCardData } from "@/lib/api/types"

const mockAgent: AgentCardData = {
  agent_id: "test-agent-1",
  name: "Test Agent",
  robotImage: "https://example.com/robot.png",
  progress: 75,
  stats: {
    users: 1245,
    robos: 1200,
    revenue: 12500,
    growth: 15,
  },
  status: "active",
}

describe("AgentCard", () => {
  it("renders agent name in aria-label", () => {
    render(<AgentCard agent={mockAgent} />)
    expect(
      screen.getByRole("article", {
        name: /Test Agent agent card/i,
      })
    ).toBeInTheDocument()
  })

  it("renders robot image", () => {
    render(<AgentCard agent={mockAgent} />)
    const img = screen.getByAltText("Test Agent")
    expect(img).toBeInTheDocument()
    expect(img).toHaveAttribute("src", "https://example.com/robot.png")
  })

  it("renders progress bar with correct width", () => {
    const { container } = render(<AgentCard agent={mockAgent} />)
    const progressFill = container.querySelector('[role="progressbar"]')
    expect(progressFill).toHaveAttribute("aria-valuenow", "75")
    expect(progressFill).toHaveStyle("width: 75%")
  })

  it("renders user stats correctly", () => {
    render(<AgentCard agent={mockAgent} />)
    expect(screen.getByText("1,245")).toBeInTheDocument()
  })

  it("renders robos currency correctly", () => {
    render(<AgentCard agent={mockAgent} />)
    expect(screen.getByText("$1.2k")).toBeInTheDocument()
  })

  it("renders revenue currency correctly", () => {
    render(<AgentCard agent={mockAgent} />)
    expect(screen.getByText("$12.5k")).toBeInTheDocument()
  })

  it("renders growth percentage in green", () => {
    const { container } = render(<AgentCard agent={mockAgent} />)
    const growthValue = screen.getByText("+15%")
    expect(growthValue).toHaveClass("text-green-400")
  })

  it("renders negative growth percentage", () => {
    const negativeAgent: AgentCardData = {
      ...mockAgent,
      stats: { ...mockAgent.stats, growth: -5 },
    }
    render(<AgentCard agent={negativeAgent} />)
    expect(screen.getByText("-5%")).toBeInTheDocument()
  })

  it("renders all stat labels", () => {
    render(<AgentCard agent={mockAgent} />)
    expect(screen.getByText("Users:")).toBeInTheDocument()
    expect(screen.getByText("Robos:")).toBeInTheDocument()
    expect(screen.getByText("Revenue:")).toBeInTheDocument()
    expect(screen.getByText("Growth:")).toBeInTheDocument()
  })

  it("handles missing robot image gracefully", () => {
    const agentWithoutImage: AgentCardData = {
      ...mockAgent,
      robotImage: undefined,
    }
    render(<AgentCard agent={agentWithoutImage} />)
    expect(screen.getByText("Test Agent")).toBeInTheDocument()
  })

  it("clamps progress bar to max 100%", () => {
    const agentWithOverProgress: AgentCardData = {
      ...mockAgent,
      progress: 150,
    }
    const { container } = render(<AgentCard agent={agentWithOverProgress} />)
    const progressFill = container.querySelector('[role="progressbar"]')
    expect(progressFill).toHaveStyle("width: 100%")
  })

  it("handles zero progress", () => {
    const agentWithZeroProgress: AgentCardData = {
      ...mockAgent,
      progress: 0,
    }
    const { container } = render(<AgentCard agent={agentWithZeroProgress} />)
    const progressFill = container.querySelector('[role="progressbar"]')
    expect(progressFill).toHaveStyle("width: 0%")
  })

  it("formats large numbers with thousands separator", () => {
    const largeAgent: AgentCardData = {
      ...mockAgent,
      stats: {
        ...mockAgent.stats,
        users: 1000000,
      },
    }
    render(<AgentCard agent={largeAgent} />)
    expect(screen.getByText("1,000,000")).toBeInTheDocument()
  })

  it("renders correct class structure for styling", () => {
    const { container } = render(<AgentCard agent={mockAgent} />)
    const card = container.firstChild
    expect(card).toHaveClass("rounded-2xl", "p-4", "flex", "flex-col")
  })
})
