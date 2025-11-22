/**
 * Not Found Page tests
 *
 * @CODE:FRONTEND-001
 * @TEST:FRONTEND-INTEGRATION-001:PHASE2:NOT-FOUND
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import NotFoundPage from './NotFoundPage'

function renderWithRouter() {
  return render(
    <MemoryRouter>
      <NotFoundPage />
    </MemoryRouter>
  )
}

describe('NotFoundPage', () => {
  it('should render 404 heading', () => {
    renderWithRouter()
    expect(screen.getByText('404')).toBeInTheDocument()
  })

  it('should render "Page Not Found" message', () => {
    renderWithRouter()
    expect(screen.getByText('Page Not Found')).toBeInTheDocument()
  })

  it('should render description text', () => {
    renderWithRouter()
    expect(screen.getByText('The page you are looking for does not exist.')).toBeInTheDocument()
  })

  it('should render "Back to Home" link', () => {
    renderWithRouter()
    const link = screen.getByText('Back to Home')
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/')
  })

  it('should have proper styling classes', () => {
    renderWithRouter()
    const heading = screen.getByText('404')
    expect(heading).toHaveClass('text-9xl', 'font-bold', 'text-gray-300')
  })
})
