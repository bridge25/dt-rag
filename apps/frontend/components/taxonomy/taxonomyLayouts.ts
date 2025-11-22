/**
 * Taxonomy layout algorithms - Dagre (tree) and D3 Force (radial)
 *
 * @CODE:FRONTEND-MIGRATION-001
 */

import * as d3Force from "d3-force"
import dagre from "dagre"
import type { Node, Edge } from "@xyflow/react"

export type LayoutType = "tree" | "radial"

interface FlowNode extends Node {
  data: {
    taxonomyNode: {
      id: string
      name: string
      level: number
      parent_id: string | null
      children?: unknown[]
    }
    isExpanded: boolean
  }
}

export function applyDagreLayout(nodes: FlowNode[], edges: Edge[]): FlowNode[] {
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))
  dagreGraph.setGraph({ rankdir: "TB" })

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 150, height: 50 })
  })

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target)
  })

  dagre.layout(dagreGraph)

  return nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id)
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 75,
        y: nodeWithPosition.y - 25,
      },
    }
  })
}

export function applyD3ForceLayout(nodes: FlowNode[], edges: Edge[]): FlowNode[] {
  // D3 Force simulation configuration
  const simulation = d3Force
    .forceSimulation(
      nodes.map((node) => ({
        id: node.id,
        x: node.position.x,
        y: node.position.y,
      }))
    )
    .force(
      "link",
      d3Force
        .forceLink(
          edges.map((edge) => ({
            source: edge.source,
            target: edge.target,
          }))
        )
        // eslint-disable-next-line
        .id((d: any) => d.id)
        .distance(100)
        .strength(0.5)
    )
    .force("charge", d3Force.forceManyBody().strength(-300))
    .force("center", d3Force.forceCenter(400, 300))
    .force("collision", d3Force.forceCollide().radius(60))
    .stop()

  // Run simulation synchronously for 300 ticks
  for (let i = 0; i < 300; i++) {
    simulation.tick()
  }

  // eslint-disable-next-line
  const simulationNodes = simulation.nodes() as any[]

  return nodes.map((node, i) => ({
    ...node,
    position: {
      x: simulationNodes[i].x - 75,
      y: simulationNodes[i].y - 25,
    },
  }))
}

export function applyLayout(
  nodes: FlowNode[],
  edges: Edge[],
  layoutType: LayoutType
): FlowNode[] {
  switch (layoutType) {
    case "tree":
      return applyDagreLayout(nodes, edges)
    case "radial":
      return applyD3ForceLayout(nodes, edges)
    default:
      return applyDagreLayout(nodes, edges)
  }
}
