import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import userEvent from "@testing-library/user-event"
import SearchPage from "../page"
import * as api from "@/lib/api"

jest.mock("@/lib/api")
const mockSearch = api.search as jest.MockedFunction<typeof api.search>

const mockSearchResults = {
  hits: Array.from({ length: 15 }, (_, i) => ({
    chunk_id: `chunk-${i}`,
    text: `Result text ${i}`,
    score: 0.9 - i * 0.01,
    metadata: {}
  }))
}

describe("@TEST:GRID-INTEGRATION - Grid Integration - Search Page", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  beforeEach(() => {
    mockSearch.mockResolvedValue(mockSearchResults)
    localStorage.clear()
  })

  it("should toggle viewMode between list and grid", async () => {
    const user = userEvent.setup()

    render(
      <QueryClientProvider client={queryClient}>
        <SearchPage />
      </QueryClientProvider>
    )

    const queryInput = screen.getByPlaceholderText(/what would you like/i)
    await user.type(queryInput, "test query")

    const searchButton = screen.getByRole("button", { name: /search/i })
    await user.click(searchButton)

    await waitFor(() => {
      expect(screen.getByText(/15/)).toBeInTheDocument()
    })

    expect(screen.getByRole("button", { name: /grid view/i })).toBeInTheDocument()

    const toggleButton = screen.getByRole("button", { name: /grid view/i })
    await user.click(toggleButton)

    expect(screen.getByRole("button", { name: /list view/i })).toBeInTheDocument()
  })

  it("should render Grid with correct layout", async () => {
    const user = userEvent.setup()

    render(
      <QueryClientProvider client={queryClient}>
        <SearchPage />
      </QueryClientProvider>
    )

    const queryInput = screen.getByPlaceholderText(/what would you like/i)
    await user.type(queryInput, "test")
    await user.click(screen.getByRole("button", { name: /search/i }))

    await waitFor(() => screen.getByText(/15/))

    const toggleButton = screen.getByRole("button", { name: /grid view/i })
    await user.click(toggleButton)

    const gridContainer = screen.getByTestId("results-grid")
    expect(gridContainer).toHaveClass("grid")
    expect(gridContainer).toHaveClass("grid-cols-12")
  })

  it("should preserve Pagination in Grid view", async () => {
    const user = userEvent.setup()

    render(
      <QueryClientProvider client={queryClient}>
        <SearchPage />
      </QueryClientProvider>
    )

    await user.type(screen.getByPlaceholderText(/what would you like/i), "test")
    await user.click(screen.getByRole("button", { name: /search/i }))

    await waitFor(() => screen.getByText(/15/))

    await user.click(screen.getByRole("button", { name: /grid view/i }))

    const page2Button = screen.getByRole("button", { name: /go to page 2/i })
    expect(page2Button).toBeInTheDocument()

    await user.click(page2Button)

    await waitFor(() => {
      expect(screen.getByText(/Result text 10/)).toBeInTheDocument()
    })
  })

  it("should sync viewMode to LocalStorage", async () => {
    const user = userEvent.setup()
    const localStorageSpy = jest.spyOn(Storage.prototype, "setItem")

    render(
      <QueryClientProvider client={queryClient}>
        <SearchPage />
      </QueryClientProvider>
    )

    await user.type(screen.getByPlaceholderText(/what would you like/i), "test")
    await user.click(screen.getByRole("button", { name: /search/i }))

    await waitFor(() => screen.getByText(/15/))

    await user.click(screen.getByRole("button", { name: /grid view/i }))

    expect(localStorageSpy).toHaveBeenCalledWith("searchViewMode", "grid")

    localStorageSpy.mockRestore()
  })
})
