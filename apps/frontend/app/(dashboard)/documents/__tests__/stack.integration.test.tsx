import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Stack } from "@/components/ui/stack"

describe("@TEST:STACK-INTEGRATION - Stack Integration - Documents Page", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  it("should render Stack with spacing=md and correct classes", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Stack spacing="md" data-testid="test-stack">
          <div>Item 1</div>
          <div>Item 2</div>
        </Stack>
      </QueryClientProvider>
    )

    const stack = screen.getByTestId("test-stack")
    expect(stack).toHaveClass("gap-4")
    expect(stack).toHaveClass("flex")
    expect(stack).toHaveClass("flex-col")
  })
})
