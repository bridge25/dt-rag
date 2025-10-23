import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import userEvent from "@testing-library/user-event"
import SearchPage from "../page"

describe("@TEST:STACK-INTEGRATION - Stack Integration - Search Page", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  it("should apply Stack with spacing=lg to Simple form", () => {
    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <SearchPage />
      </QueryClientProvider>
    )

    const simpleForm = container.querySelector("form")
    expect(simpleForm).toBeInTheDocument()

    const stack = simpleForm?.firstChild as HTMLElement
    expect(stack).toHaveClass("gap-6")
  })

  it("should apply Stack with spacing=lg to Advanced form", async () => {
    const user = userEvent.setup()

    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <SearchPage />
      </QueryClientProvider>
    )

    const advancedTab = screen.getByRole("tab", { name: /advanced/i })
    await user.click(advancedTab)

    const forms = container.querySelectorAll("form")
    const advancedForm = forms[forms.length - 1]

    const stack = advancedForm.firstChild as HTMLElement
    expect(stack).toHaveClass("gap-6")
  })
})
