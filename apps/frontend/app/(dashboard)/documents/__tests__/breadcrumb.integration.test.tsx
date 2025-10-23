import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import DocumentsPage from "../page"

describe("@TEST:BREADCRUMB-INTEGRATION - Breadcrumb Integration - Documents Page", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  it("should render breadcrumb with correct links", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <DocumentsPage />
      </QueryClientProvider>
    )

    const breadcrumb = screen.getByRole("navigation", { name: /breadcrumb/i })
    expect(breadcrumb).toBeInTheDocument()

    const dashboardLink = screen.getByRole("link", { name: "Dashboard" })
    expect(dashboardLink).toBeInTheDocument()
    expect(dashboardLink).toHaveAttribute("href", "/dashboard")

    const documentsLabel = breadcrumb.querySelector("span")
    expect(documentsLabel).toHaveTextContent("Documents")
  })
})
