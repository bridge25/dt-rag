import { render, screen } from '@testing-library/react'
import { Progress } from '../Progress'

describe('Progress', () => {
  test('renders with correct value', () => {
    render(<Progress value={50} />)
    const progressBar = screen.getByRole('progressbar')
    expect(progressBar).toHaveAttribute('aria-valuenow', '50')
  })

  test('renders with label', () => {
    render(<Progress value={75} showLabel />)
    expect(screen.getByText('75%')).toBeInTheDocument()
  })

  test('handles boundary values', () => {
    const { rerender } = render(<Progress value={0} />)
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0')

    rerender(<Progress value={100} />)
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100')
  })

  test('clamps values outside 0-100 range', () => {
    const { rerender } = render(<Progress value={-10} />)
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0')

    rerender(<Progress value={150} />)
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100')
  })

  test('renders with different color variants', () => {
    const { rerender, container } = render(<Progress value={50} color="primary" />)
    const progressBar = container.querySelector('[style*="width: 50%"]')
    expect(progressBar).toBeInTheDocument()

    rerender(<Progress value={50} color="accent" />)
    expect(container.querySelector('[style*="width: 50%"]')).toBeInTheDocument()
  })
})
