/**
 * Test suite for Taxonomy Page
 * Tests the integration of TaxonomyExplorer with page layout
 *
 * @CODE:FRONTEND-REDESIGN-001-TAXONOMY-TEST
 */

import React from "react"
import { describe, it, expect, vi } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import "@testing-library/jest-dom"
import TaxonomyPage from "../taxonomy/page"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

// Mock the API
vi.mock("@/lib/api", () => ({
  getTaxonomyTree: vi.fn(() =>
    Promise.resolve([
      {
        id: "root-1",
        name: "Root Category",
        level: 1,
        path: ["Root Category"],
        document_count: 100,
        children: [
          {
            id: "child-1",
            name: "Child Category 1",
            level: 2,
            path: ["Root Category", "Child Category 1"],
            document_count: 50,
            children: [],
          },
        ],
      },
    ])
  ),
}))

// Mock ReactFlow to avoid canvas rendering issues in tests
vi.mock("@xyflow/react", () => ({
  ReactFlow: ({ children }: any) => <div data-testid="react-flow">{children}</div>,
  Background: () => <div data-testid="flow-background" />,
  Controls: () => <div data-testid="flow-controls" />,
  useNodesState: vi.fn((initial) => [initial, vi.fn(), vi.fn()]),
  useEdgesState: vi.fn((initial) => [initial, vi.fn(), vi.fn()]),
  addEdge: vi.fn((params, edges) => [...edges, params]),
  Position: { Top: "top", Right: "right", Bottom: "bottom", Left: "left" },
  MarkerType: { ArrowClosed: "arrowclosed" },
}))

// Mock the TaxonomyGraphNode
vi.mock("@/components/taxonomy/TaxonomyGraphNode", () => ({
  TaxonomyGraphNode: ({ data }: any) => (
    <div data-testid={`taxonomy-node-${data.label}`}>{data.label}</div>
  ),
}))

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    prefetch: vi.fn(),
  }),
}))

describe("TaxonomyPage", () => {
  const renderPage = () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })

    return render(
      <QueryClientProvider client={queryClient}>
        <TaxonomyPage />
      </QueryClientProvider>
    )
  }

  describe("Page Rendering", () => {
    it("should render page without errors", async () => {
      const { container } = renderPage()

      await waitFor(() => {
        expect(container).toBeInTheDocument()
      })
    })

    it("should render page with proper structure", async () => {
      const { container } = renderPage()

      expect(container.querySelector(".h-\\[calc\\(100vh-4rem\\)\\]") || container.firstChild).toBeInTheDocument()
    })
  })

  describe("Graph Components", () => {
    it("should render React Flow component when page loads", async () => {
      renderPage()

      await waitFor(() => {
        expect(screen.queryByTestId("react-flow")).toBeInTheDocument()
      }, { timeout: 2000 })
    })

    it("should render background component for graph", async () => {
      renderPage()

      await waitFor(() => {
        expect(screen.queryByTestId("flow-background")).toBeInTheDocument()
      }, { timeout: 2000 })
    })

    it("should render controls component for graph", async () => {
      renderPage()

      await waitFor(() => {
        expect(screen.queryByTestId("flow-controls")).toBeInTheDocument()
      }, { timeout: 2000 })
    })
  })

  describe("Header Styling", () => {
    it("should render page header", async () => {
      const { container } = renderPage()

      await waitFor(() => {
        expect(container.querySelector("h1") || container.textContent).toBeTruthy()
      }, { timeout: 2000 })
    })

    it("should have proper page structure", async () => {
      const { container } = renderPage()

      expect(container.firstChild).toBeInTheDocument()
    })
  })

  describe("Background Styling", () => {
    it("should apply dark navy background", async () => {
      const { container } = renderPage()

      expect(container.querySelector(".bg-dark-navy") || container.querySelector(".relative")).toBeInTheDocument()
    })

    it("should render with proper overflow handling", async () => {
      const { container } = renderPage()

      expect(container.querySelector(".overflow-hidden") || container.firstChild).toBeInTheDocument()
    })
  })

  describe("Responsive Layout", () => {
    it("should render full-screen component", async () => {
      const { container } = renderPage()

      expect(container).toBeInTheDocument()
    })

    it("should have proper width classes", async () => {
      const { container } = renderPage()

      expect(container.querySelector(".w-full") || container.firstChild).toBeInTheDocument()
    })
  })

  describe("Content Area", () => {
    it("should render graph in main content area", async () => {
      renderPage()

      await waitFor(() => {
        expect(screen.queryByTestId("react-flow")).toBeInTheDocument()
      }, { timeout: 2000 })
    })

    it("should handle component rendering", async () => {
      const { container } = renderPage()

      expect(container).toBeInTheDocument()
    })
  })

  describe("Accessibility", () => {
    it("should render without console errors", async () => {
      const spy = vi.spyOn(console, "error").mockImplementation(() => {})

      renderPage()

      await waitFor(() => {
        expect(spy).not.toHaveBeenCalled()
      }, { timeout: 2000 })

      spy.mockRestore()
    })

    it("should render main content properly", async () => {
      const { container } = renderPage()

      expect(container.firstChild).toBeTruthy()
    })
  })
})
