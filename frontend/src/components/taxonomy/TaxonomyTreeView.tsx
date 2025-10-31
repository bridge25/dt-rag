// @CODE:TAXONOMY-VIZ-001-003
// TaxonomyTreeView component - React Flow canvas with Dagre layout

import { useCallback, useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from '@xyflow/react'
import { useQuery } from '@tanstack/react-query'
import dagre from 'dagre'
import { fetchTaxonomyTree } from '../../lib/api/taxonomy'
import type { TaxonomyNode } from '../../lib/api/types'
import '@xyflow/react/dist/style.css'

interface FlowNode extends Node {
  data: {
    taxonomyNode: TaxonomyNode
    isExpanded: boolean
  }
}

function convertTaxonomyToFlow(
  taxonomyNode: TaxonomyNode
): { nodes: FlowNode[]; edges: Edge[] } {
  const nodes: FlowNode[] = []
  const edges: Edge[] = []

  function traverse(node: TaxonomyNode) {
    nodes.push({
      id: node.id,
      type: 'default',
      position: { x: 0, y: 0 }, // Will be calculated by Dagre
      data: {
        taxonomyNode: node,
        isExpanded: true,
      },
    })

    if (node.children) {
      for (const child of node.children) {
        edges.push({
          id: `${node.id}-${child.id}`,
          source: node.id,
          target: child.id,
          type: 'default',
        })
        traverse(child)
      }
    }
  }

  traverse(taxonomyNode)
  return { nodes, edges }
}

function applyDagreLayout(nodes: FlowNode[], edges: Edge[]): FlowNode[] {
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))
  dagreGraph.setGraph({ rankdir: 'TB' })

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

export default function TaxonomyTreeView() {
  const {
    data: taxonomyData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['taxonomy', 'tree'],
    queryFn: () => fetchTaxonomyTree(),
    staleTime: 5 * 60 * 1000,
    retry: 3,
  })

  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!taxonomyData) {
      return { nodes: [], edges: [] }
    }
    const { nodes, edges } = convertTaxonomyToFlow(taxonomyData)
    const layoutedNodes = applyDagreLayout(nodes, edges)
    return { nodes: layoutedNodes, edges }
  }, [taxonomyData])

  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)

  const onInit = useCallback(() => {
    // React Flow initialization callback
  }, [])

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-gray-500">Loading taxonomy tree...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-red-500">
          Error loading taxonomy: {error.message}
        </p>
      </div>
    )
  }

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onInit={onInit}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  )
}
