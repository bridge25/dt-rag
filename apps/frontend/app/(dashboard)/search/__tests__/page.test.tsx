import React from "react"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import SearchPage from "../page"
import { search } from "@/lib/api"

jest.mock("@/lib/api", () => ({
  search: jest.fn(),
}))

const mockSearchFn = search as jest.MockedFunction<typeof search>

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  )
}

const mockSearchResults = (count: number) => ({
  hits: Array.from({ length: count }, (_, i) => ({
    chunk_id: `chunk-${i + 1}`,
    score: 0.9 - i * 0.01,
    text: `Test result ${i + 1} content`,
    source: {
      url: `https://example.com/doc${i + 1}`,
      title: `Document ${i + 1}`,
      date: "2024-01-01",
    },
    taxonomy_path: ["test", "category"],
    metadata: { key: `value${i + 1}` },
  })),
  latency: 150,
  request_id: "test-request-id",
  total_candidates: count,
})

describe("SPEC-UI-INTEGRATION-001: Spinner & Pagination Integration", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe("@TEST:UI-INTEGRATION-001:SPINNER - AC-1: Spinner Integration", () => {
    test("shows Spinner when search is pending", async () => {
      mockSearchFn.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockSearchResults(5)), 100))
      )

      renderWithQueryClient(<SearchPage />)

      const input = screen.getByPlaceholderText("What would you like to search for?")
      const submitButton = screen.getByRole("button", { name: /search/i })

      await userEvent.type(input, "test query")
      await userEvent.click(submitButton)

      expect(screen.getByRole("status", { name: /loading/i })).toBeInTheDocument()
    })

    test("shows \"Search\" text when search is not pending", () => {
      renderWithQueryClient(<SearchPage />)

      const submitButton = screen.getByRole("button", { name: /search/i })
      expect(submitButton).toHaveTextContent("Search")
    })

    test("Spinner has correct size and color props", async () => {
      mockSearchFn.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockSearchResults(5)), 100))
      )

      renderWithQueryClient(<SearchPage />)

      const input = screen.getByPlaceholderText("What would you like to search for?")
      const submitButton = screen.getByRole("button", { name: /search/i })

      await userEvent.type(input, "test query")
      await userEvent.click(submitButton)

      const spinner = screen.getByRole("status", { name: /loading/i })
      expect(spinner).toHaveClass("w-4", "h-4")
      expect(spinner).toHaveClass("border-white")
    })

    test("screen reader text \"Searching...\" exists during pending state", async () => {
      mockSearchFn.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockSearchResults(5)), 100))
      )

      renderWithQueryClient(<SearchPage />)

      const input = screen.getByPlaceholderText("What would you like to search for?")
      const submitButton = screen.getByRole("button", { name: /search/i })

      await userEvent.type(input, "test query")
      await userEvent.click(submitButton)

      expect(screen.getByText("Searching...")).toHaveClass("sr-only")
    })
  })

  describe("@TEST:UI-INTEGRATION-001:PAGINATION - AC-2: Pagination Integration", () => {
    test("shows Pagination when results > 10", async () => {
      mockSearchFn.mockResolvedValue(mockSearchResults(15))

      renderWithQueryClient(<SearchPage />)

      const input = screen.getByPlaceholderText("What would you like to search for?")
      const submitButton = screen.getByRole("button", { name: /search/i })

      await userEvent.type(input, "test query")
      await userEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByLabelText("Pagination")).toBeInTheDocument()
      })
    })

    test("does NOT show Pagination when results <= 10", async () => {
      mockSearchFn.mockResolvedValue(mockSearchResults(8))

      renderWithQueryClient(<SearchPage />)

      const input = screen.getByPlaceholderText("What would you like to search for?")
      const submitButton = screen.getByRole("button", { name: /search/i })

      await userEvent.type(input, "test query")
      await userEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText("8")).toBeInTheDocument()
      })

      expect(screen.queryByLabelText("Pagination")).not.toBeInTheDocument()
    })

    test("displays correct page 1 results (items 1-10)", async () => {
      mockSearchFn.mockResolvedValue(mockSearchResults(25))

      renderWithQueryClient(<SearchPage />)

      const input = screen.getByPlaceholderText("What would you like to search for?")
      const submitButton = screen.getByRole("button", { name: /search/i })

      await userEvent.type(input, "test query")
      await userEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText("Test result 1 content")).toBeInTheDocument()
      })

      expect(screen.getByText("Test result 1 content")).toBeInTheDocument()
      expect(screen.getByText("Test result 10 content")).toBeInTheDocument()
      expect(screen.queryByText("Test result 11 content")).not.toBeInTheDocument()
    })

    test("displays correct page 2 results (items 11-20) after page change", async () => {
      mockSearchFn.mockResolvedValue(mockSearchResults(25))

      renderWithQueryClient(<SearchPage />)

      const input = screen.getByPlaceholderText("What would you like to search for?")
      const submitButton = screen.getByRole("button", { name: /search/i })

      await userEvent.type(input, "test query")
      await userEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByLabelText("Pagination")).toBeInTheDocument()
      })

      const page2Button = screen.getByRole("button", { name: /go to page 2/i })
      await userEvent.click(page2Button)

      await waitFor(() => {
        expect(screen.getByText("Test result 11 content")).toBeInTheDocument()
      })

      expect(screen.getByText("Test result 11 content")).toBeInTheDocument()
      expect(screen.getByText("Test result 20 content")).toBeInTheDocument()
      expect(screen.queryByText("Test result 10 content")).not.toBeInTheDocument()
    })

    test("calculates totalPages correctly (Math.ceil(hits.length / 10))", async () => {
      mockSearchFn.mockResolvedValue(mockSearchResults(25))

      renderWithQueryClient(<SearchPage />)

      const input = screen.getByPlaceholderText("What would you like to search for?")
      const submitButton = screen.getByRole("button", { name: /search/i })

      await userEvent.type(input, "test query")
      await userEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByLabelText("Pagination")).toBeInTheDocument()
      })

      expect(screen.getByRole("button", { name: /go to page 3/i })).toBeInTheDocument()
      expect(screen.queryByRole("button", { name: /go to page 4/i })).not.toBeInTheDocument()
    })

    test("resets to page 1 on new search", async () => {
      mockSearchFn.mockResolvedValue(mockSearchResults(25))

      renderWithQueryClient(<SearchPage />)

      const input = screen.getByPlaceholderText("What would you like to search for?")
      const submitButton = screen.getByRole("button", { name: /search/i })

      await userEvent.type(input, "first query")
      await userEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByLabelText("Pagination")).toBeInTheDocument()
      })

      const page2Button = screen.getByRole("button", { name: /go to page 2/i })
      await userEvent.click(page2Button)

      await waitFor(() => {
        expect(screen.getByText("Test result 11 content")).toBeInTheDocument()
      })

      await userEvent.clear(input)
      await userEvent.type(input, "second query")
      await userEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText("Test result 1 content")).toBeInTheDocument()
      })

      expect(screen.getByRole("button", { name: /current page 1/i })).toBeInTheDocument()
    })
  })
})
