/**
 * LoadingSpinner Component Tests
 * @TEST:FRONTEND-MIGRATION-001
 */

import { describe, it, expect } from "vitest"
import { render } from "@testing-library/react"
import { LoadingSpinner } from "../LoadingSpinner"

describe("LoadingSpinner", () => {
  it("renders a loading spinner", () => {
    const { container } = render(<LoadingSpinner />)

    const spinner = container.querySelector(".animate-spin")
    expect(spinner).toBeInTheDocument()
  })

  it("has centered layout", () => {
    const { container } = render(<LoadingSpinner />)

    const wrapper = container.firstChild as HTMLElement
    expect(wrapper).toHaveClass("flex", "items-center", "justify-center")
  })

  it("has correct spinner dimensions", () => {
    const { container } = render(<LoadingSpinner />)

    const spinnerContainer = container.querySelector(".relative")
    expect(spinnerContainer).toHaveClass("w-16", "h-16")
  })
})
