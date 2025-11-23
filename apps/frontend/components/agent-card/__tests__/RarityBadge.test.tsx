/**
 * RarityBadge Component Tests
 * @TEST:FRONTEND-MIGRATION-001
 */

import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { RarityBadge } from "../RarityBadge"

describe("RarityBadge", () => {
  it("renders Common rarity", () => {
    render(<RarityBadge rarity="Common" />)
    expect(screen.getByText("Common")).toBeInTheDocument()
  })

  it("renders Rare rarity with blue background", () => {
    const { container } = render(<RarityBadge rarity="Rare" />)
    expect(container.firstChild).toHaveClass("bg-blue-500")
  })

  it("renders Epic rarity with purple background", () => {
    const { container } = render(<RarityBadge rarity="Epic" />)
    expect(container.firstChild).toHaveClass("bg-purple-600")
  })

  it("renders Legendary rarity with amber background", () => {
    const { container } = render(<RarityBadge rarity="Legendary" />)
    expect(container.firstChild).toHaveClass("bg-amber-500")
  })

  it("has correct aria-label", () => {
    render(<RarityBadge rarity="Epic" />)
    expect(screen.getByLabelText("Rarity: Epic")).toBeInTheDocument()
  })

  it("applies custom className", () => {
    const { container } = render(
      <RarityBadge rarity="Common" className="custom-class" />
    )
    expect(container.firstChild).toHaveClass("custom-class")
  })
})
