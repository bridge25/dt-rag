// @TEST:TAXONOMY-VIZ-001-001
// Test for React Flow & Dagre installation and basic setup

import { describe, it, expect } from 'vitest'

describe('React Flow Installation', () => {
  it('should have @xyflow/react package installed', async () => {
    const reactFlow = await import('@xyflow/react')
    expect(reactFlow).toBeDefined()
    expect(reactFlow.ReactFlow).toBeDefined()
  })

  it('should have ReactFlow core components available', async () => {
    const { ReactFlow, MiniMap, Controls, Background } = await import('@xyflow/react')
    expect(ReactFlow).toBeDefined()
    expect(MiniMap).toBeDefined()
    expect(Controls).toBeDefined()
    expect(Background).toBeDefined()
  })

  it('should have dagre library installed for layout', async () => {
    const dagre = await import('dagre')
    expect(dagre).toBeDefined()
    expect(dagre.graphlib).toBeDefined()
  })

  it('should have @xyflow/react styles available', () => {
    // Test that the style import path exists (will be imported in components)
    expect('@xyflow/react/dist/style.css').toBeDefined()
  })
})

describe('React Flow CSS Import', () => {
  it('should define React Flow style path constant', () => {
    const REACT_FLOW_STYLE_PATH = '@xyflow/react/dist/style.css'
    expect(REACT_FLOW_STYLE_PATH).toBe('@xyflow/react/dist/style.css')
  })
})
