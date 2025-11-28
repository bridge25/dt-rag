/**
 * AgentCardGrid Component Tests - Ethereal Glass Design
 * Testing responsive grid layout, empty states, and card rendering
 * @TEST:FRONTEND-REDESIGN-001
 */

import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import React from "react"
import { AgentCardGrid } from "../AgentCardGrid"
import type { AgentCardData } from "@/lib/api/types"

describe("AgentCardGrid", () => {
  const mockAgents: AgentCardData[] = [
    {
      agent_id: "1",
      name: "Analyst",
      robotImage: "/robots/analyst.png",
      progress: 75,
      stats: {
        users: 1245,
        robos: 1250,
        revenue: 12500,
        growth: 15,
      },
      status: "active",
    },
    {
      agent_id: "2",
      name: "Innovator",
      robotImage: "/robots/innovator.png",
      progress: 85,
      stats: {
        users: 2340,
        robos: 2500,
        revenue: 25000,
        growth: 22,
      },
      status: "active",
    },
    {
      agent_id: "3",
      name: "Researcher",
      robotImage: "/robots/researcher.png",
      progress: 60,
      stats: {
        users: 1560,
        robos: 1800,
        revenue: 18000,
        growth: 18,
      },
      status: "active",
    },
  ]

  describe("Rendering agents", () => {
    it("should render correct number of agent cards", () => {
      const { container } = render(<AgentCardGrid agents={mockAgents} />)
      const cards = container.querySelectorAll("[data-testid^='agent-card-']")
      expect(cards).toHaveLength(3)
    })

    it("should display agent names as data attributes", () => {
      const { container } = render(<AgentCardGrid agents={mockAgents} />)
      const card1 = container.querySelector("[data-agent-name='Analyst']")
      const card2 = container.querySelector("[data-agent-name='Innovator']")
      const card3 = container.querySelector("[data-agent-name='Researcher']")

      expect(card1).toBeInTheDocument()
      expect(card2).toBeInTheDocument()
      expect(card3).toBeInTheDocument()
    })

    it("should render agent cards with correct test IDs", () => {
      const { container } = render(<AgentCardGrid agents={mockAgents} />)
      expect(container.querySelector("[data-testid='agent-card-1']")).toBeInTheDocument()
      expect(container.querySelector("[data-testid='agent-card-2']")).toBeInTheDocument()
      expect(container.querySelector("[data-testid='agent-card-3']")).toBeInTheDocument()
    })
  })

  describe("Empty state handling", () => {
    it("should show empty state message when no agents provided", () => {
      render(<AgentCardGrid agents={[]} />)
      expect(screen.getByText(/no agents/i)).toBeInTheDocument()
    })

    it("should not render any agent cards when agents list is empty", () => {
      const { container } = render(<AgentCardGrid agents={[]} />)
      const cards = container.querySelectorAll("[data-testid^='agent-card-']")
      expect(cards).toHaveLength(0)
    })

    it("should show helpful message in empty state", () => {
      render(<AgentCardGrid agents={[]} />)
      expect(
        screen.getByText(/create or import agents to get started/i)
      ).toBeInTheDocument()
    })
  })

  describe("Responsive grid layout", () => {
    it("should have responsive grid classes for 5-column layout", () => {
      const { container } = render(<AgentCardGrid agents={mockAgents} />)
      const grid = container.querySelector("[class*='grid']") as HTMLElement
      expect(grid).toBeInTheDocument()
      expect(grid.className).toContain("grid-cols-1")
      expect(grid.className).toContain("sm:grid-cols-2")
      expect(grid.className).toContain("md:grid-cols-3")
      expect(grid.className).toContain("lg:grid-cols-4")
      expect(grid.className).toContain("xl:grid-cols-5")
    })

    it("should have proper gap between grid items", () => {
      const { container } = render(<AgentCardGrid agents={mockAgents} />)
      const grid = container.querySelector("[class*='grid']") as HTMLElement
      expect(grid.className).toContain("gap-4")
    })

    it("should be full width", () => {
      const { container } = render(<AgentCardGrid agents={mockAgents} />)
      const grid = container.querySelector("[class*='grid']") as HTMLElement
      expect(grid.className).toContain("w-full")
    })
  })

  describe("Animation and styling", () => {
    it("should have animation wrapper elements", () => {
      const { container } = render(<AgentCardGrid agents={mockAgents} />)
      const cards = container.querySelectorAll("[data-testid^='agent-card-']")

      // Each card should be wrapped in an animation container
      cards.forEach((card) => {
        const animationWrapper = card.parentElement as HTMLElement
        expect(animationWrapper).toBeDefined()
        expect(animationWrapper.className).toBeTruthy()
      })
    })

    it("should define fadeInZoom keyframe animation", () => {
      const { container } = render(<AgentCardGrid agents={mockAgents} />)
      const style = container.querySelector("style")
      expect(style?.textContent).toContain("@keyframes fadeInZoom")
      expect(style?.textContent).toContain("opacity: 0")
      expect(style?.textContent).toContain("transform: scale(0.95)")
    })
  })

  describe("Semantic HTML and accessibility", () => {
    it("should have semantic section element", () => {
      const { container } = render(<AgentCardGrid agents={mockAgents} />)
      const section = container.querySelector("section")
      expect(section).toBeInTheDocument()
    })

    it("should have proper ARIA label", () => {
      const { container } = render(<AgentCardGrid agents={mockAgents} />)
      const section = container.querySelector("section")
      expect(section).toHaveAttribute("aria-label", "Agent cards grid")
    })

    it("should support custom className prop", () => {
      const { container } = render(
        <AgentCardGrid agents={mockAgents} className="custom-class" />
      )
      const section = container.querySelector("section")
      expect(section).toHaveClass("custom-class")
    })
  })

  describe("Memoization and performance", () => {
    it("should handle multiple render cycles with same agents", () => {
      const { rerender, container } = render(<AgentCardGrid agents={mockAgents} />)
      let cards = container.querySelectorAll("[data-testid^='agent-card-']")
      expect(cards).toHaveLength(3)

      // Rerender with same props
      rerender(<AgentCardGrid agents={mockAgents} />)

      cards = container.querySelectorAll("[data-testid^='agent-card-']")
      expect(cards).toHaveLength(3)
    })

    it("should update when agent list changes", () => {
      const { rerender, container } = render(
        <AgentCardGrid agents={[mockAgents[0]]} />
      )

      let cards = container.querySelectorAll("[data-testid^='agent-card-']")
      expect(cards).toHaveLength(1)

      // Rerender with different agents
      rerender(<AgentCardGrid agents={mockAgents} />)

      cards = container.querySelectorAll("[data-testid^='agent-card-']")
      expect(cards).toHaveLength(3)
    })

    it("should update when progress changes", () => {
      const agentsV1 = mockAgents.map((a) => ({
        ...a,
        progress: 50,
      }))

      const agentsV2 = mockAgents.map((a) => ({
        ...a,
        progress: 75,
      }))

      const { rerender, container } = render(
        <AgentCardGrid agents={agentsV1} />
      )

      expect(container.querySelectorAll("[data-testid^='agent-card-']")).toHaveLength(3)

      // Rerender with different progress
      rerender(<AgentCardGrid agents={agentsV2} />)

      expect(container.querySelectorAll("[data-testid^='agent-card-']")).toHaveLength(3)
    })
  })

  describe("RefForwardRef support", () => {
    it("should support ref forwarding", () => {
      const ref = React.createRef<HTMLDivElement>()
      render(<AgentCardGrid agents={mockAgents} ref={ref} />)
      expect(ref.current).toBeInstanceOf(HTMLElement)
    })
  })

  describe("Single agent rendering", () => {
    it("should render single agent correctly", () => {
      const { container } = render(
        <AgentCardGrid agents={[mockAgents[0]]} />
      )
      const cards = container.querySelectorAll("[data-testid^='agent-card-']")
      expect(cards).toHaveLength(1)
    })
  })

  describe("Large agent list rendering", () => {
    it("should handle large agent lists", () => {
      const largeAgentList = Array.from({ length: 50 }, (_, i) => ({
        ...mockAgents[0],
        agent_id: `large-${i}`,
        name: `Agent ${i}`,
      }))

      const { container } = render(<AgentCardGrid agents={largeAgentList} />)
      const cards = container.querySelectorAll("[data-testid^='agent-card-']")
      expect(cards).toHaveLength(50)
    })
  })
})
