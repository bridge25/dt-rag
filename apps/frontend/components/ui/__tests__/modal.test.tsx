import { describe, test, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { Modal } from "../modal"

describe("Modal", () => {
  test("renders when open", () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="Test Modal">
        <p>Modal Content</p>
      </Modal>
    )
    expect(screen.getByText("Test Modal")).toBeInTheDocument()
    expect(screen.getByText("Modal Content")).toBeInTheDocument()
  })

  test("does not render when closed", () => {
    render(
      <Modal isOpen={false} onClose={vi.fn()} title="Test Modal">
        <p>Modal Content</p>
      </Modal>
    )
    expect(screen.queryByText("Test Modal")).not.toBeInTheDocument()
  })

  test("closes on ESC key", () => {
    const onClose = vi.fn()
    render(
      <Modal isOpen={true} onClose={onClose} title="Test Modal">
        <p>Modal Content</p>
      </Modal>
    )

    fireEvent.keyDown(document, { key: "Escape" })
    expect(onClose).toHaveBeenCalled()
  })

  test("closes on backdrop click", () => {
    const onClose = vi.fn()
    render(
      <Modal isOpen={true} onClose={onClose} title="Test Modal">
        <p>Modal Content</p>
      </Modal>
    )

    const backdrop = screen.getByTestId("modal-backdrop")
    fireEvent.click(backdrop)
    expect(onClose).toHaveBeenCalled()
  })

  test("closes on X button click", () => {
    const onClose = vi.fn()
    render(
      <Modal isOpen={true} onClose={onClose} title="Test Modal">
        <p>Modal Content</p>
      </Modal>
    )

    const closeButton = screen.getByLabelText("Close")
    fireEvent.click(closeButton)
    expect(onClose).toHaveBeenCalled()
  })

  test("renders without title", () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()}>
        <p>Modal Content</p>
      </Modal>
    )
    expect(screen.getByText("Modal Content")).toBeInTheDocument()
    expect(screen.queryByRole("heading")).not.toBeInTheDocument()
  })
})
