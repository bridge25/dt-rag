import { render, screen } from '@testing-library/react'
import { Container } from '../Container'

describe('Container', () => {
  test('renders children', () => {
    render(
      <Container>
        <p>Test content</p>
      </Container>
    )
    expect(screen.getByText('Test content')).toBeInTheDocument()
  })

  test('applies default max-width', () => {
    const { container } = render(
      <Container>
        <p>Content</p>
      </Container>
    )
    const containerElement = container.firstChild as HTMLElement
    expect(containerElement).toHaveClass('max-w-7xl')
  })

  test('applies glass morphism when enabled', () => {
    const { container } = render(
      <Container glass>
        <p>Content</p>
      </Container>
    )
    const containerElement = container.firstChild as HTMLElement
    expect(containerElement).toHaveClass('backdrop-blur-lg')
  })

  test('does not apply glass morphism by default', () => {
    const { container } = render(
      <Container>
        <p>Content</p>
      </Container>
    )
    const containerElement = container.firstChild as HTMLElement
    expect(containerElement).not.toHaveClass('backdrop-blur-lg')
  })

  test('applies custom className', () => {
    const { container } = render(
      <Container className="custom-class">
        <p>Content</p>
      </Container>
    )
    const containerElement = container.firstChild as HTMLElement
    expect(containerElement).toHaveClass('custom-class')
  })

  test('centers content by default', () => {
    const { container } = render(
      <Container>
        <p>Content</p>
      </Container>
    )
    const containerElement = container.firstChild as HTMLElement
    expect(containerElement).toHaveClass('mx-auto')
  })
})
