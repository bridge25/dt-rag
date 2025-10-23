import { render } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import SearchPage from "../page"

describe("@TEST:CONTAINER-INTEGRATION - Container Integration - Search Page", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  it("should apply max-width 7xl container", () => {
    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <SearchPage />
      </QueryClientProvider>
    )

    const rootDiv = container.firstChild as HTMLElement
    expect(rootDiv).toHaveClass("max-w-7xl")
  })

  it("should apply responsive horizontal padding", () => {
    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <SearchPage />
      </QueryClientProvider>
    )

    const rootDiv = container.firstChild as HTMLElement
    expect(rootDiv).toHaveClass("px-4")
  })

  it("should center content with mx-auto", () => {
    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <SearchPage />
      </QueryClientProvider>
    )

    const rootDiv = container.firstChild as HTMLElement
    expect(rootDiv).toHaveClass("mx-auto")
  })
})
