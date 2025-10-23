import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import SearchPage from "../page"

describe("@TEST:TABS-INTEGRATION - Tabs Integration", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  it("should switch between simple and advanced tabs", async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <SearchPage />
      </QueryClientProvider>
    )

    expect(screen.queryByLabelText("Top K Results")).not.toBeInTheDocument()

    const advancedTab = screen.getByRole("tab", { name: /advanced/i })
    await userEvent.click(advancedTab)

    expect(screen.getByLabelText("Top K Results")).toBeInTheDocument()
    expect(screen.getByLabelText(/Use Hybrid/i)).toBeInTheDocument()
  })

  it("should preserve query input on tab switch", async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <SearchPage />
      </QueryClientProvider>
    )

    const simpleTab = screen.getByRole("tab", { name: /simple/i })
    await userEvent.click(simpleTab)

    const queryInputSimple = screen.getByPlaceholderText(/what would you like/i)
    await userEvent.type(queryInputSimple, "test query")

    const advancedTab = screen.getByRole("tab", { name: /advanced/i })
    await userEvent.click(advancedTab)

    const queryInputAdvanced = screen.getByPlaceholderText(/what would you like/i)
    expect(queryInputAdvanced).toHaveValue("test query")

    await userEvent.click(simpleTab)

    expect(queryInputSimple).toHaveValue("test query")
  })
})
