import { render, screen } from '@testing-library/react'
import { Stack } from '../Stack'

describe('Stack', () => {
  test('renders children', () => {
    render(
      <Stack>
        <div>Item 1</div>
        <div>Item 2</div>
      </Stack>
    )
    expect(screen.getByText('Item 1')).toBeInTheDocument()
    expect(screen.getByText('Item 2')).toBeInTheDocument()
  })

  test('applies vertical direction by default', () => {
    const { container } = render(
      <Stack>
        <div>Item</div>
      </Stack>
    )
    const stackElement = container.firstChild as HTMLElement
    expect(stackElement).toHaveClass('flex-col')
  })

  test('applies horizontal direction', () => {
    const { container } = render(
      <Stack direction="horizontal">
        <div>Item</div>
      </Stack>
    )
    const stackElement = container.firstChild as HTMLElement
    expect(stackElement).toHaveClass('flex-row')
  })

  test('applies spacing - xs', () => {
    const { container } = render(
      <Stack spacing="xs">
        <div>Item</div>
      </Stack>
    )
    const stackElement = container.firstChild as HTMLElement
    expect(stackElement).toHaveClass('gap-1')
  })

  test('applies spacing - sm', () => {
    const { container } = render(
      <Stack spacing="sm">
        <div>Item</div>
      </Stack>
    )
    const stackElement = container.firstChild as HTMLElement
    expect(stackElement).toHaveClass('gap-2')
  })

  test('applies spacing - md', () => {
    const { container } = render(
      <Stack spacing="md">
        <div>Item</div>
      </Stack>
    )
    const stackElement = container.firstChild as HTMLElement
    expect(stackElement).toHaveClass('gap-4')
  })

  test('applies spacing - lg', () => {
    const { container } = render(
      <Stack spacing="lg">
        <div>Item</div>
      </Stack>
    )
    const stackElement = container.firstChild as HTMLElement
    expect(stackElement).toHaveClass('gap-6')
  })

  test('applies spacing - xl', () => {
    const { container } = render(
      <Stack spacing="xl">
        <div>Item</div>
      </Stack>
    )
    const stackElement = container.firstChild as HTMLElement
    expect(stackElement).toHaveClass('gap-8')
  })

  test('applies custom className', () => {
    const { container } = render(
      <Stack className="custom-stack">
        <div>Item</div>
      </Stack>
    )
    const stackElement = container.firstChild as HTMLElement
    expect(stackElement).toHaveClass('custom-stack')
  })

  test('applies alignment', () => {
    const { container } = render(
      <Stack align="center">
        <div>Item</div>
      </Stack>
    )
    const stackElement = container.firstChild as HTMLElement
    expect(stackElement).toHaveClass('items-center')
  })

  test('applies justification', () => {
    const { container } = render(
      <Stack justify="between">
        <div>Item</div>
      </Stack>
    )
    const stackElement = container.firstChild as HTMLElement
    expect(stackElement).toHaveClass('justify-between')
  })
})
