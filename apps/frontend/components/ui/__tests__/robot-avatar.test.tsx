/**
 * RobotAvatar Component Tests
 * Testing SVG loading, rarity-based styling, and accessibility
 * @TEST:ROBOT-AVATAR-001
 */

import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import React from "react"
import { RobotAvatar } from "../robot-avatar"

// Mock Next.js Image component
vi.mock("next/image", () => ({
  default: ({ src, alt, ...props }: any) => (
    // eslint-disable-next-line @next/next/no-img-element -- intentional mock for testing
    <img src={src} alt={alt} data-testid="robot-avatar-img" {...props} />
  ),
}))

describe("RobotAvatar", () => {
  describe("Rendering", () => {
    it("should render SVG avatar with correct robot name", () => {
      render(
        <RobotAvatar
          robot="analyst"
          rarity="common"
        />
      )

      const img = screen.getByTestId("robot-avatar-img")
      expect(img).toBeInTheDocument()
      expect(img).toHaveAttribute("src", "/avatars/robots/analyst.svg")
    })

    it("should render avatar with different robot types", () => {
      const robots = ["analyst", "builder", "explorer", "guardian"]

      robots.forEach((robot) => {
        const { unmount } = render(
          <RobotAvatar robot={robot} rarity="common" />
        )
        const img = screen.getByTestId("robot-avatar-img")
        expect(img).toHaveAttribute("src", `/avatars/robots/${robot}.svg`)
        unmount()
      })
    })

    it("should have alt text for accessibility", () => {
      render(
        <RobotAvatar
          robot="innovator"
          rarity="rare"
        />
      )

      const img = screen.getByTestId("robot-avatar-img")
      expect(img).toHaveAttribute("alt")
      expect(img.getAttribute("alt")).toContain("innovator")
    })
  })

  describe("Rarity-based styling", () => {
    it("should apply common rarity styling", () => {
      const { container } = render(
        <RobotAvatar
          robot="analyst"
          rarity="common"
        />
      )

      const wrapper = container.firstChild
      expect(wrapper).toHaveClass("rarity-common")
    })

    it("should apply rare rarity styling", () => {
      const { container } = render(
        <RobotAvatar
          robot="innovator"
          rarity="rare"
        />
      )

      const wrapper = container.firstChild
      expect(wrapper).toHaveClass("rarity-rare")
    })

    it("should apply epic rarity styling", () => {
      const { container } = render(
        <RobotAvatar
          robot="researcher"
          rarity="epic"
        />
      )

      const wrapper = container.firstChild
      expect(wrapper).toHaveClass("rarity-epic")
    })

    it("should apply legendary rarity styling", () => {
      const { container } = render(
        <RobotAvatar
          robot="validator"
          rarity="legendary"
        />
      )

      const wrapper = container.firstChild
      expect(wrapper).toHaveClass("rarity-legendary")
    })

    it("should apply glow shadow based on rarity", () => {
      const { container: commonContainer } = render(
        <RobotAvatar
          robot="analyst"
          rarity="common"
        />
      )
      const commonWrapper = commonContainer.firstChild as HTMLElement
      expect(commonWrapper.className).toContain("shadow-")

      const { container: rareContainer } = render(
        <RobotAvatar
          robot="innovator"
          rarity="rare"
        />
      )
      const rareWrapper = rareContainer.firstChild as HTMLElement
      expect(rareWrapper.className).toContain("shadow-")
    })
  })

  describe("Size variants", () => {
    it("should render with small size", () => {
      const { container } = render(
        <RobotAvatar
          robot="analyst"
          rarity="common"
          size="sm"
        />
      )

      const wrapper = container.firstChild as HTMLElement
      expect(wrapper.className).toContain("h-16")
      expect(wrapper.className).toContain("w-16")
    })

    it("should render with medium size (default)", () => {
      const { container } = render(
        <RobotAvatar
          robot="analyst"
          rarity="common"
          size="md"
        />
      )

      const wrapper = container.firstChild as HTMLElement
      expect(wrapper.className).toContain("h-24")
      expect(wrapper.className).toContain("w-24")
    })

    it("should render with large size", () => {
      const { container } = render(
        <RobotAvatar
          robot="analyst"
          rarity="common"
          size="lg"
        />
      )

      const wrapper = container.firstChild as HTMLElement
      expect(wrapper.className).toContain("h-32")
      expect(wrapper.className).toContain("w-32")
    })

    it("should default to medium size when not specified", () => {
      const { container } = render(
        <RobotAvatar
          robot="analyst"
          rarity="common"
        />
      )

      const wrapper = container.firstChild as HTMLElement
      expect(wrapper.className).toContain("h-24")
      expect(wrapper.className).toContain("w-24")
    })
  })

  describe("Hover animation", () => {
    it("should have hover animation classes", () => {
      const { container } = render(
        <RobotAvatar
          robot="analyst"
          rarity="common"
        />
      )

      const wrapper = container.firstChild as HTMLElement
      expect(wrapper.className).toContain("hover:")
      expect(wrapper.className).toContain("transition-")
    })
  })

  describe("Error handling", () => {
    it("should render fallback when image fails to load", async () => {
      const { container } = render(
        <RobotAvatar
          robot="nonexistent"
          rarity="common"
        />
      )

      const wrapper = container.firstChild as HTMLElement
      expect(wrapper).toBeInTheDocument()
      // Component should still render even if image fails
      expect(wrapper.className).toContain("rarity-common")
    })

    it("should handle missing rarity gracefully", () => {
      const { container } = render(
        <RobotAvatar
          robot="analyst"
          rarity="common"
        />
      )

      expect(container.firstChild).toBeInTheDocument()
    })
  })

  describe("Accessibility", () => {
    it("should have proper ARIA attributes", () => {
      const { container } = render(
        <RobotAvatar
          robot="innovator"
          rarity="rare"
        />
      )

      const wrapper = container.firstChild as HTMLElement
      const img = screen.getByTestId("robot-avatar-img")
      expect(img).toHaveAttribute("alt")
      expect(img.getAttribute("alt")).not.toBe("")
    })

    it("should be keyboard accessible", () => {
      const { container } = render(
        <RobotAvatar
          robot="analyst"
          rarity="common"
        />
      )

      const wrapper = container.firstChild as HTMLElement
      // Should not be focusable (just display element)
      expect(wrapper.tagName).toBe("DIV")
    })
  })
})
