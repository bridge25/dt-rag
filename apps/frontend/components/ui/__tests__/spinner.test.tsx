import { render, screen } from "@testing-library/react"
import { Spinner } from "../spinner"

describe("Spinner", () => {
  test("renders with correct size - small", () => {
    render(<Spinner size="sm" />)
    const spinner = screen.getByRole("status")
    expect(spinner).toHaveClass("w-4", "h-4")
  })

  test("renders with correct size - medium", () => {
    render(<Spinner size="md" />)
    const spinner = screen.getByRole("status")
    expect(spinner).toHaveClass("w-6", "h-6")
  })

  test("renders with correct size - large", () => {
    render(<Spinner size="lg" />)
    const spinner = screen.getByRole("status")
    expect(spinner).toHaveClass("w-8", "h-8")
  })

  test("renders with primary color", () => {
    render(<Spinner color="primary" />)
    const spinner = screen.getByRole("status")
    expect(spinner).toHaveClass("border-primary-600")
  })

  test("renders with white color", () => {
    render(<Spinner color="white" />)
    const spinner = screen.getByRole("status")
    expect(spinner).toHaveClass("border-white")
  })

  test("has accessible label", () => {
    render(<Spinner />)
    const spinner = screen.getByRole("status")
    expect(spinner).toHaveAttribute("aria-label", "Loading")
  })

  test("has screen reader text", () => {
    render(<Spinner />)
    expect(screen.getByText("Loading...")).toBeInTheDocument()
  })

  test("uses default size and color", () => {
    render(<Spinner />)
    const spinner = screen.getByRole("status")
    expect(spinner).toHaveClass("w-6", "h-6", "border-primary-600")
  })
})
