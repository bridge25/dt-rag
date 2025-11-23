/**
 * ProgressBar Component Tests
 * @TEST:FRONTEND-MIGRATION-001
 */

import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { ProgressBar } from "../ProgressBar"

describe("ProgressBar", () => {
  it("renders progressbar role", () => {
    render(<ProgressBar current={50} max={100} />)
    expect(screen.getByRole("progressbar")).toBeInTheDocument()
  })

  it("displays correct aria values", () => {
    render(<ProgressBar current={30} max={100} />)
    const progressbar = screen.getByRole("progressbar")
    expect(progressbar).toHaveAttribute("aria-valuenow", "30")
    expect(progressbar).toHaveAttribute("aria-valuemax", "100")
    expect(progressbar).toHaveAttribute("aria-valuemin", "0")
  })

  it("renders label when provided", () => {
    render(<ProgressBar current={50} max={100} label="50/100 XP" />)
    expect(screen.getByText("50/100 XP")).toBeInTheDocument()
  })

  it("does not render label when not provided", () => {
    const { container } = render(<ProgressBar current={50} max={100} />)
    expect(container.querySelector("p")).not.toBeInTheDocument()
  })

  it("calculates correct percentage", () => {
    const { container } = render(<ProgressBar current={75} max={100} />)
    const progressFill = container.querySelector("[style]")
    expect(progressFill).toHaveStyle({ width: "75%" })
  })

  it("caps percentage at 100%", () => {
    const { container } = render(<ProgressBar current={150} max={100} />)
    const progressFill = container.querySelector("[style]")
    expect(progressFill).toHaveStyle({ width: "100%" })
  })

  it("handles zero max value", () => {
    const { container } = render(<ProgressBar current={50} max={0} />)
    const progressFill = container.querySelector("[style]")
    expect(progressFill).toHaveStyle({ width: "0%" })
  })

  it("applies custom ariaLabel", () => {
    render(
      <ProgressBar current={50} max={100} ariaLabel="Experience progress" />
    )
    expect(screen.getByLabelText("Experience progress")).toBeInTheDocument()
  })
})
