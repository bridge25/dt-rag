import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Tooltip } from '../Tooltip'

describe('Tooltip', () => {
  test('renders trigger element', () => {
    render(
      <Tooltip content="Tooltip text">
        <button>Hover me</button>
      </Tooltip>
    )
    expect(screen.getByText('Hover me')).toBeInTheDocument()
  })

  test('shows tooltip on hover after delay', async () => {
    const user = userEvent.setup()
    render(
      <Tooltip content="Tooltip text">
        <button>Hover me</button>
      </Tooltip>
    )

    const trigger = screen.getByText('Hover me')
    await user.hover(trigger)

    await waitFor(() => {
      expect(screen.getByText('Tooltip text')).toBeInTheDocument()
    })
  })

  test('hides tooltip on mouse leave', async () => {
    const user = userEvent.setup()
    render(
      <Tooltip content="Tooltip text">
        <button>Hover me</button>
      </Tooltip>
    )

    const trigger = screen.getByText('Hover me')
    await user.hover(trigger)

    await waitFor(() => {
      expect(screen.getByText('Tooltip text')).toBeInTheDocument()
    })

    await user.unhover(trigger)

    await waitFor(() => {
      expect(screen.queryByText('Tooltip text')).not.toBeInTheDocument()
    })
  })

  test('renders in different positions', () => {
    const { rerender } = render(
      <Tooltip content="Tooltip text" position="top">
        <button>Hover me</button>
      </Tooltip>
    )
    expect(screen.getByText('Hover me')).toBeInTheDocument()

    rerender(
      <Tooltip content="Tooltip text" position="bottom">
        <button>Hover me</button>
      </Tooltip>
    )
    expect(screen.getByText('Hover me')).toBeInTheDocument()

    rerender(
      <Tooltip content="Tooltip text" position="left">
        <button>Hover me</button>
      </Tooltip>
    )
    expect(screen.getByText('Hover me')).toBeInTheDocument()

    rerender(
      <Tooltip content="Tooltip text" position="right">
        <button>Hover me</button>
      </Tooltip>
    )
    expect(screen.getByText('Hover me')).toBeInTheDocument()
  })
})
