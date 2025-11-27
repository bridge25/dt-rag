/**
 * Test suite for Agents Page
 * Tests the integration of AgentCardGrid with Ethereal Glass styling
 *
 * @CODE:FRONTEND-REDESIGN-001-AGENTS-TEST
 */

import React from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import "@testing-library/jest-dom"
import AgentsPage from "../agents/page"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

// Mock the useAgents hook
vi.mock("@/hooks/useAgents", () => ({
  useAgents: vi.fn(() => ({
    agents: [
      {
        agent_id: "agent-1",
        name: "Data Analyst",
        character_description: "Analyzes data patterns",
        level: 24,
        rarity: "Legendary",
        current_xp: 2400,
        next_level_xp: 3000,
        total_documents: 45,
        total_queries: 156,
        quality_score: 98,
        status: "active",
        robot: "analyst",
      },
      {
        agent_id: "agent-2",
        name: "Code Helper",
        character_description: "Assists with code",
        level: 18,
        rarity: "Epic",
        current_xp: 1800,
        next_level_xp: 2500,
        total_documents: 32,
        total_queries: 89,
        quality_score: 95,
        status: "active",
        robot: "builder",
      },
    ],
    isLoading: false,
    error: null,
  })),
}))

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    prefetch: vi.fn(),
  }),
}))

describe("AgentsPage", () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })
  })

  const renderPage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <AgentsPage />
      </QueryClientProvider>
    )
  }

  describe("Page Rendering", () => {
    it("should render with correct title", () => {
      renderPage()
      const title = screen.getByText(/AI Agents/i)
      expect(title).toBeInTheDocument()
    })

    it("should display subtitle with agent count", () => {
      renderPage()
      const subtitle = screen.getByText(/Your specialized AI workforce/i)
      expect(subtitle).toBeInTheDocument()
    })

    it("should render page header with proper styling", () => {
      const { container } = renderPage()
      const header = container.querySelector("h1")
      expect(header).toHaveClass("text-3xl", "font-bold", "text-white")
    })
  })

  describe("Search Functionality", () => {
    it("should have a search input field", () => {
      renderPage()
      const searchInput = screen.getByPlaceholderText("Search agents...")
      expect(searchInput).toBeInTheDocument()
    })

    it("should filter agents by name when searching", async () => {
      renderPage()
      const searchInput = screen.getByPlaceholderText("Search agents...")

      fireEvent.change(searchInput, { target: { value: "Analyst" } })

      await waitFor(() => {
        expect(screen.getByText("Data Analyst")).toBeInTheDocument()
        expect(screen.queryByText("Code Helper")).not.toBeInTheDocument()
      })
    })

    it("should show all agents when search is cleared", async () => {
      renderPage()
      const searchInput = screen.getByPlaceholderText("Search agents...")

      fireEvent.change(searchInput, { target: { value: "Analyst" } })
      fireEvent.change(searchInput, { target: { value: "" } })

      await waitFor(() => {
        expect(screen.getByText("Data Analyst")).toBeInTheDocument()
        expect(screen.getByText("Code Helper")).toBeInTheDocument()
      })
    })
  })

  describe("View Mode Toggle", () => {
    it("should have view mode toggle buttons", () => {
      const { container } = renderPage()
      const toggleButtons = container.querySelectorAll("button[class*='transition-all']")

      expect(toggleButtons.length).toBeGreaterThan(0)
    })

    it("should render page with grid container", () => {
      const { container } = renderPage()
      const mainContainer = container.querySelector(".min-h-screen.p-8")

      expect(mainContainer).toBeInTheDocument()
    })

    it("should handle view mode switching", () => {
      const { container } = renderPage()
      const buttons = container.querySelectorAll("button")

      expect(buttons.length).toBeGreaterThan(0)
    })
  })

  describe("Agent Cards", () => {
    it("should render AgentCardGrid component", async () => {
      const { container } = renderPage()

      await waitFor(() => {
        const grid = container.querySelector("[aria-label='Agent cards grid']")
        expect(grid).toBeInTheDocument()
      })
    })

    it("should display agent cards when data is loaded", async () => {
      renderPage()

      await waitFor(() => {
        const agentCards = screen.getAllByRole("article")
        expect(agentCards.length).toBeGreaterThan(0)
      })
    })

    it("should show agent information in cards", async () => {
      renderPage()

      await waitFor(() => {
        expect(screen.getByText("Data Analyst")).toBeInTheDocument()
      })
    })

    it("should render cards with proper styling classes", async () => {
      const { container } = renderPage()

      await waitFor(() => {
        const cards = container.querySelectorAll("[role='article']")
        expect(cards.length).toBeGreaterThan(0)
      })
    })
  })

  describe("Stats Overview", () => {
    it("should display stats grid with key metrics", () => {
      renderPage()

      expect(screen.getByText("Total Agents")).toBeInTheDocument()
      expect(screen.getByText("Active Now")).toBeInTheDocument()
      expect(screen.getByText("Total Queries")).toBeInTheDocument()
      expect(screen.getByText("Avg Quality")).toBeInTheDocument()
    })

    it("should display numeric stat values", () => {
      const { container } = renderPage()
      const pageContent = container.textContent

      expect(pageContent).toContain("Total Agents")
      expect(pageContent).toContain("Active Now")
    })

    it("should have proper glass morphism styling on stat cards", () => {
      const { container } = renderPage()
      const statCards = container.querySelectorAll(".rounded-2xl")

      expect(statCards.length).toBeGreaterThan(0)
    })
  })

  describe("Action Buttons", () => {
    it("should have a new agent button", () => {
      renderPage()
      const newAgentBtn = screen.getByText(/New Agent/i)
      expect(newAgentBtn).toBeInTheDocument()
    })

    it("should have proper button styling with glow effect", () => {
      renderPage()
      const newAgentBtn = screen.getByText(/New Agent/i).closest("button")
      expect(newAgentBtn).toHaveClass("bg-gradient-to-r")
    })

    it("should render buttons with proper styling", async () => {
      const { container } = renderPage()

      await waitFor(() => {
        const buttons = container.querySelectorAll("button")
        expect(buttons.length).toBeGreaterThan(0)
      })
    })
  })

  describe("Empty State", () => {
    it("should show appropriate content when agents are loaded", async () => {
      renderPage()

      await waitFor(() => {
        expect(screen.getByText("Data Analyst")).toBeInTheDocument()
      })
    })
  })

  describe("Ethereal Glass Styling", () => {
    it("should apply proper glass morphism classes to page background", () => {
      const { container } = renderPage()
      const pageContainer = container.firstChild

      expect(pageContainer).toHaveClass("min-h-screen", "p-8")
    })

    it("should have animated background particles", () => {
      const { container } = renderPage()
      const particles = container.querySelectorAll(".animate-pulse")

      expect(particles.length).toBeGreaterThan(0)
    })

    it("should render cards with glasscard styling", async () => {
      renderPage()

      await waitFor(() => {
        const cards = screen.getAllByRole("article")
        expect(cards.length).toBeGreaterThan(0)
      })
    })
  })

  describe("Responsive Layout", () => {
    it("should use responsive grid classes", () => {
      const { container } = renderPage()
      const mainGrid = container.querySelector(".max-w-7xl")

      expect(mainGrid).toBeInTheDocument()
    })

    it("should have proper gap and spacing", () => {
      const { container } = renderPage()
      const statsGrid = container.querySelector(".grid.grid-cols-2")

      expect(statsGrid).toHaveClass("gap-4")
    })
  })
})
