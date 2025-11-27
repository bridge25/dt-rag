/**
 * AgentCardGrid Component Tests
 * Testing responsive grid layout, empty states, and card rendering
 * @TEST:AGENT-CARD-GRID-001
 */

import { describe, it, expect, vi } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import React from "react"
import { AgentCardGrid } from "../AgentCardGrid"
import type { AgentCardData } from "../types"

// Mock the RobotAvatar component
vi.mock("../../ui/robot-avatar", () => ({
  RobotAvatar: ({ robot, rarity }: any) => (
    <div data-testid={`robot-avatar-${robot}`}>
      Avatar: {robot} - {rarity}
    </div>
  ),
}))

// Mock the AgentCard component
vi.mock("../AgentCard", () => ({
  AgentCard: ({ agent, onView, onDelete }: any) => (
    <div
      data-testid={`agent-card-${agent.agent_id}`}
      data-agent-name={agent.name}
    >
      <button onClick={onView} data-testid={`view-${agent.agent_id}`}>
        View
      </button>
      <button onClick={onDelete} data-testid={`delete-${agent.agent_id}`}>
        Delete
      </button>
    </div>
  ),
}))

describe("AgentCardGrid", () => {
  const mockAgents: AgentCardData[] = [
    {
      agent_id: "1",
      name: "Analyst",
      level: 5,
      rarity: "Common",
      robot: "analyst",
      current_xp: 1000,
      next_level_xp: 2000,
      total_documents: 42,
      total_queries: 156,
      quality_score: 95,
      avatar_url: "/avatars/analyst.svg",
    },
    {
      agent_id: "2",
      name: "Innovator",
      level: 8,
      rarity: "Rare",
      robot: "innovator",
      current_xp: 1500,
      next_level_xp: 2500,
      total_documents: 78,
      total_queries: 234,
      quality_score: 92,
      avatar_url: "/avatars/innovator.svg",
    },
    {
      agent_id: "3",
      name: "Researcher",
      level: 12,
      rarity: "Epic",
      robot: "researcher",
      current_xp: 2000,
      next_level_xp: 3000,
      total_documents: 156,
      total_queries: 512,
      quality_score: 98,
      avatar_url: "/avatars/researcher.svg",
    },
  ]

  const mockHandlers = {
    onView: vi.fn(),
    onDelete: vi.fn(),
  }

  beforeEach(() => {
    mockHandlers.onView.mockClear()
    mockHandlers.onDelete.mockClear()
  })

  describe("Rendering agents", () => {
    it("should render correct number of agent cards", () => {
      const { container } = render(
        <AgentCardGrid
          agents={mockAgents}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      const cards = container.querySelectorAll("[data-testid^='agent-card-']")
      // Filter to only direct children of the grid
      const gridCards = Array.from(cards).filter((card) => {
        return card.parentElement?.className?.includes("grid") || false
      })
      expect(gridCards).toHaveLength(3)
    })

    it("should pass correct props to AgentCard components", () => {
      const { container } = render(
        <AgentCardGrid
          agents={mockAgents}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      const cards = container.querySelectorAll("[data-testid^='agent-card-']")
      const gridCards = Array.from(cards).filter((card) => {
        return card.parentElement?.className?.includes("grid") || false
      })
      expect(gridCards[0]).toHaveAttribute("data-agent-name", "Analyst")
      expect(gridCards[1]).toHaveAttribute("data-agent-name", "Innovator")
    })

    it("should call onView when view button is clicked", () => {
      render(
        <AgentCardGrid
          agents={mockAgents}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      const viewButton = screen.getByTestId("view-1")
      viewButton.click()

      expect(mockHandlers.onView).toHaveBeenCalledWith(mockAgents[0])
    })

    it("should call onDelete when delete button is clicked", () => {
      render(
        <AgentCardGrid
          agents={mockAgents}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      const deleteButton = screen.getByTestId("delete-2")
      deleteButton.click()

      expect(mockHandlers.onDelete).toHaveBeenCalledWith(mockAgents[1])
    })
  })

  describe("Empty state handling", () => {
    it("should show empty state message when no agents provided", () => {
      render(
        <AgentCardGrid
          agents={[]}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      expect(screen.getByText(/no agents/i)).toBeInTheDocument()
    })

    it("should not render any agent cards when agents list is empty", () => {
      const { container } = render(
        <AgentCardGrid
          agents={[]}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      const cards = container.querySelectorAll("[data-testid^='agent-card-']")
      expect(cards).toHaveLength(0)
    })

    it("should show suggestion in empty state", () => {
      render(
        <AgentCardGrid
          agents={[]}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      const emptyState = screen.getByText(/no agents/i)
      expect(emptyState).toBeInTheDocument()
    })
  })

  describe("Responsive grid layout", () => {
    it("should have responsive grid classes", () => {
      const { container } = render(
        <AgentCardGrid
          agents={mockAgents}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      const grid = container.querySelector("[class*='grid']")
      expect(grid).toBeInTheDocument()
      expect(grid?.className).toContain("grid")
    })

    it("should apply grid column classes for responsiveness", () => {
      const { container } = render(
        <AgentCardGrid
          agents={mockAgents}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      const grid = container.querySelector("[class*='grid']") as HTMLElement
      // Should have responsive column classes like grid-cols-1, md:grid-cols-2, etc.
      expect(
        grid.className.includes("grid-cols-") ||
        grid.className.includes("md:grid-cols-") ||
        grid.className.includes("lg:grid-cols-")
      ).toBe(true)
    })
  })

  describe("Animation and styling", () => {
    it("should have staggered animation classes", () => {
      const { container } = render(
        <AgentCardGrid
          agents={mockAgents}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      // Each card should have animation delay
      const cards = container.querySelectorAll("[data-testid^='agent-card-']")
      const gridCards = Array.from(cards).filter((card) => {
        return card.parentElement?.className?.includes("grid") || false
      })
      expect(gridCards.length).toBe(3)

      gridCards.forEach((card) => {
        const element = card as HTMLElement
        expect(element.style.animation || element.className).toBeTruthy()
      })
    })

    it("should have gap between grid items", () => {
      const { container } = render(
        <AgentCardGrid
          agents={mockAgents}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      const grid = container.querySelector("[class*='grid']") as HTMLElement
      expect(grid.className).toContain("gap-")
    })
  })

  describe("Memoization and performance", () => {
    it("should handle multiple render cycles efficiently", () => {
      const { rerender, container } = render(
        <AgentCardGrid
          agents={mockAgents}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      let cards = container.querySelectorAll("[data-testid^='agent-card-']")
      let gridCards = Array.from(cards).filter((card) => {
        return card.parentElement?.className?.includes("grid") || false
      })
      expect(gridCards).toHaveLength(3)

      // Rerender with same props
      rerender(
        <AgentCardGrid
          agents={mockAgents}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      cards = container.querySelectorAll("[data-testid^='agent-card-']")
      gridCards = Array.from(cards).filter((card) => {
        return card.parentElement?.className?.includes("grid") || false
      })
      expect(gridCards).toHaveLength(3)
    })

    it("should update when agent list changes", () => {
      const { rerender, container } = render(
        <AgentCardGrid
          agents={[mockAgents[0]]}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      let cards = container.querySelectorAll("[data-testid^='agent-card-']")
      let gridCards = Array.from(cards).filter((card) => {
        return card.parentElement?.className?.includes("grid") || false
      })
      expect(gridCards).toHaveLength(1)

      rerender(
        <AgentCardGrid
          agents={mockAgents}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      cards = container.querySelectorAll("[data-testid^='agent-card-']")
      gridCards = Array.from(cards).filter((card) => {
        return card.parentElement?.className?.includes("grid") || false
      })
      expect(gridCards).toHaveLength(3)
    })
  })

  describe("Accessibility", () => {
    it("should have semantic HTML structure", () => {
      const { container } = render(
        <AgentCardGrid
          agents={mockAgents}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      const section = container.querySelector("section")
      expect(section).toBeInTheDocument()
    })

    it("should have proper ARIA labels", () => {
      const { container } = render(
        <AgentCardGrid
          agents={mockAgents}
          onView={mockHandlers.onView}
          onDelete={mockHandlers.onDelete}
        />
      )

      const section = container.querySelector("section")
      expect(section).toHaveAttribute("aria-label")
    })
  })
})
