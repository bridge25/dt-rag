// @TEST:AGENT-CARD-001-UI-004
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { ActionButtons } from '../ActionButtons'

describe('ActionButtons', () => {
  it('should render View button', () => {
    render(<ActionButtons onView={() => {}} onDelete={() => {}} />)
    expect(screen.getByText('View')).toBeInTheDocument()
  })

  it('should render Delete button', () => {
    render(<ActionButtons onView={() => {}} onDelete={() => {}} />)
    expect(screen.getByText('Delete')).toBeInTheDocument()
  })

  it('should call onView when View button is clicked', async () => {
    const user = userEvent.setup()
    const onView = vi.fn()
    render(<ActionButtons onView={onView} onDelete={() => {}} />)

    await user.click(screen.getByText('View'))
    expect(onView).toHaveBeenCalledTimes(1)
  })

  it('should call onDelete when Delete button is clicked', async () => {
    const user = userEvent.setup()
    const onDelete = vi.fn()
    render(<ActionButtons onView={() => {}} onDelete={onDelete} />)

    await user.click(screen.getByText('Delete'))
    expect(onDelete).toHaveBeenCalledTimes(1)
  })
})
