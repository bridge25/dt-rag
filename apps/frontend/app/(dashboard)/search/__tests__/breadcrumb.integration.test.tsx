import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import SearchPage from "../page"

describe("@TEST:BREADCRUMB-INTEGRATION - Breadcrumb Integration - Search Page", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  it("should render breadcrumb with correct links", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <SearchPage />
      </QueryClientProvider>
    )

    const breadcrumb = screen.getByRole("navigation", { name: /breadcrumb/i })
    expect(breadcrumb).toBeInTheDocument()

    const dashboardLink = screen.getByRole("link", { name: "Dashboard" })
    expect(dashboardLink).toBeInTheDocument()
    expect(dashboardLink.tagName).toBe("A")
    expect(dashboardLink).toHaveAttribute("href", "/dashboard")

    const searchLabel = breadcrumb.querySelector("span")
    expect(searchLabel).toHaveTextContent("Search")
  })

  it("should show current page without link", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <SearchPage />
      </QueryClientProvider>
    )

    const breadcrumb = screen.getByRole("navigation", { name: /breadcrumb/i })
    const currentPage = breadcrumb.querySelector("span")

    expect(currentPage?.tagName).toBe("SPAN")
  })
})
