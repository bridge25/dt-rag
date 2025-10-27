import { render, screen } from '@testing-library/react'
import { Grid, GridItem } from '../Grid'

describe('Grid', () => {
  test('renders children', () => {
    render(
      <Grid>
        <div>Item 1</div>
        <div>Item 2</div>
      </Grid>
    )
    expect(screen.getByText('Item 1')).toBeInTheDocument()
    expect(screen.getByText('Item 2')).toBeInTheDocument()
  })

  test('applies default 12-column grid', () => {
    const { container } = render(
      <Grid>
        <div>Item</div>
      </Grid>
    )
    const gridElement = container.firstChild as HTMLElement
    expect(gridElement).toHaveClass('grid-cols-12')
  })

  test('applies gap spacing', () => {
    const { container } = render(
      <Grid gap="md">
        <div>Item</div>
      </Grid>
    )
    const gridElement = container.firstChild as HTMLElement
    expect(gridElement).toHaveClass('gap-4')
  })

  test('applies different gap sizes', () => {
    const { rerender, container } = render(
      <Grid gap="xs">
        <div>Item</div>
      </Grid>
    )
    expect((container.firstChild as HTMLElement)).toHaveClass('gap-1')

    rerender(
      <Grid gap="sm">
        <div>Item</div>
      </Grid>
    )
    expect((container.firstChild as HTMLElement)).toHaveClass('gap-2')

    rerender(
      <Grid gap="lg">
        <div>Item</div>
      </Grid>
    )
    expect((container.firstChild as HTMLElement)).toHaveClass('gap-6')
  })

  test('applies custom className', () => {
    const { container } = render(
      <Grid className="custom-grid">
        <div>Item</div>
      </Grid>
    )
    const gridElement = container.firstChild as HTMLElement
    expect(gridElement).toHaveClass('custom-grid')
  })
})

describe('GridItem', () => {
  test('renders children', () => {
    render(
      <GridItem>
        <p>Grid item content</p>
      </GridItem>
    )
    expect(screen.getByText('Grid item content')).toBeInTheDocument()
  })

  test('applies column span', () => {
    const { container } = render(
      <GridItem colSpan={6}>
        <p>Content</p>
      </GridItem>
    )
    const itemElement = container.firstChild as HTMLElement
    expect(itemElement).toHaveClass('col-span-6')
  })

  test('applies different column spans', () => {
    const { rerender, container } = render(
      <GridItem colSpan={3}>
        <p>Content</p>
      </GridItem>
    )
    expect((container.firstChild as HTMLElement)).toHaveClass('col-span-3')

    rerender(
      <GridItem colSpan={12}>
        <p>Content</p>
      </GridItem>
    )
    expect((container.firstChild as HTMLElement)).toHaveClass('col-span-12')
  })
})
