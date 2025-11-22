/**
 * ErrorBoundary Component Tests
 * @TEST:FRONTEND-MIGRATION-001
 */

import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { ErrorBoundary } from "../ErrorBoundary"

// Component that throws an error
function ThrowError({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error("Test error message")
  }
  return <div>Content without error</div>
}

describe("ErrorBoundary", () => {
  // Suppress console.error for these tests
  const originalError = console.error
  beforeAll(() => {
    console.error = vi.fn()
  })
  afterAll(() => {
    console.error = originalError
  })

  it("renders children when no error", () => {
    render(
      <ErrorBoundary>
        <div>Test content</div>
      </ErrorBoundary>
    )

    expect(screen.getByText("Test content")).toBeInTheDocument()
  })

  it("renders error UI when child throws", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText("Something went wrong")).toBeInTheDocument()
    expect(screen.getByText("Test error message")).toBeInTheDocument()
  })

  it("renders custom fallback when provided", () => {
    render(
      <ErrorBoundary fallback={<div>Custom error fallback</div>}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText("Custom error fallback")).toBeInTheDocument()
  })

  it("shows try again button in default error UI", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument()
  })
})
