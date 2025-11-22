/**
 * StatCard Component Tests
 * @TEST:FRONTEND-MIGRATION-001
 */

import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { StatCard } from "../StatCard"
import { Bot } from "lucide-react"

describe("StatCard", () => {
  it("renders title", () => {
    render(
      <StatCard title="Total Agents" value={5} icon={<Bot />} />
    )
    expect(screen.getByText("Total Agents")).toBeInTheDocument()
  })

  it("renders numeric value", () => {
    render(
      <StatCard title="Documents" value={42} icon={<Bot />} />
    )
    expect(screen.getByText("42")).toBeInTheDocument()
  })

  it("renders string value", () => {
    render(
      <StatCard title="Status" value="Active" icon={<Bot />} />
    )
    expect(screen.getByText("Active")).toBeInTheDocument()
  })

  it("renders description when provided", () => {
    render(
      <StatCard
        title="Agents"
        value={3}
        icon={<Bot />}
        description="Active agents in your workspace"
      />
    )
    expect(
      screen.getByText("Active agents in your workspace")
    ).toBeInTheDocument()
  })

  it("does not render description when not provided", () => {
    render(
      <StatCard title="Agents" value={3} icon={<Bot />} />
    )
    // Description element should not be present
    expect(document.querySelector(".text-xs.text-gray-500")).not.toBeInTheDocument()
  })

  it("renders icon", () => {
    const { container } = render(
      <StatCard title="Test" value={1} icon={<Bot data-testid="icon" />} />
    )
    expect(screen.getByTestId("icon")).toBeInTheDocument()
  })
})
