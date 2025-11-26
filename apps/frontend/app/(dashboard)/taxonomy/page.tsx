/**
 * Taxonomy browser page - Constellation Graph View
 *
 * @CODE:FRONTEND-MIGRATION-002
 */

"use client";

import { useCallback, useMemo } from 'react';
import { useQuery } from "@tanstack/react-query";
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  Position,
  MarkerType
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';

import { getTaxonomyTree } from "@/lib/api";
import { TaxonomyGraphNode } from "@/components/taxonomy/TaxonomyGraphNode";
import { IconBadge } from "@/components/ui/icon-badge";
import { Network, Loader2 } from "lucide-react";

// Node Types Configuration
const nodeTypes = {
  taxonomyNode: TaxonomyGraphNode,
};

// Layout Calculation using Dagre
const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  dagreGraph.setGraph({ rankdir: 'TB', nodesep: 100, ranksep: 150 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 80, height: 80 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 40,
        y: nodeWithPosition.y - 40,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

// Transform API data to React Flow elements
const transformDataToGraph = (data: any[]) => {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  const traverse = (item: any, parentId: string | null = null) => {
    const nodeId = item.id;

    nodes.push({
      id: nodeId,
      type: 'taxonomyNode',
      data: {
        label: item.name,
        type: item.level === 1 ? 'root' : item.children?.length ? 'category' : 'item',
        count: item.children?.length
      },
      position: { x: 0, y: 0 }, // Initial position, will be calculated by dagre
    });

    if (parentId) {
      edges.push({
        id: `e${parentId}-${nodeId}`,
        source: parentId,
        target: nodeId,
        type: 'default',
        animated: true,
        style: { stroke: 'rgba(255, 255, 255, 0.2)', strokeWidth: 1 },
      });
    }

    if (item.children) {
      item.children.forEach((child: any) => traverse(child, nodeId));
    }
  };

  data.forEach(root => traverse(root));

  return getLayoutedElements(nodes, edges);
};

export default function TaxonomyPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["taxonomy"],
    queryFn: () => getTaxonomyTree("1.8.1"),
  });

  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!data) return { nodes: [], edges: [] };
    return transformDataToGraph(data);
  }, [data]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update graph when data loads
  useMemo(() => {
    if (data) {
      const { nodes: layoutedNodes, edges: layoutedEdges } = transformDataToGraph(data);
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    }
  }, [data, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-dark-navy">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-12 w-12 animate-spin text-accent-glow-blue" />
          <p className="text-gray-400 animate-pulse">Mapping the constellation...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-screen items-center justify-center bg-dark-navy">
        <div className="text-center space-y-4">
          <div className="inline-flex p-4 rounded-full bg-red-500/10 border border-red-500/20">
            <Network className="h-8 w-8 text-red-500" />
          </div>
          <h2 className="text-xl font-bold text-white">Failed to load taxonomy</h2>
          <p className="text-gray-400">Could not retrieve the star chart data.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-4rem)] w-full bg-dark-navy relative overflow-hidden">
      {/* Header Overlay */}
      <div className="absolute top-6 left-8 z-10 pointer-events-none">
        <div className="flex items-center gap-4">
          <IconBadge icon={Network} color="blue" size="lg" className="bg-glass border-white/10 backdrop-blur-md" />
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white drop-shadow-lg">Taxonomy Constellation</h1>
            <p className="text-gray-300 drop-shadow-md">
              Interactive knowledge graph visualization
            </p>
          </div>
        </div>
      </div>

      {/* React Flow Graph */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        className="bg-dark-navy"
        minZoom={0.1}
        maxZoom={1.5}
        defaultEdgeOptions={{
          type: 'default',
          animated: true,
          style: { stroke: 'rgba(255, 255, 255, 0.15)', strokeWidth: 1.5 },
        }}
      >
        <Background
          color="#4a5568"
          gap={20}
          size={1}
          className="opacity-20"
        />
        <Controls
          className="bg-glass border border-white/10 text-white fill-white [&>button]:border-b-white/10 [&>button:hover]:bg-white/10"
        />
      </ReactFlow>

      {/* Ambient Particles (CSS only for performance) */}
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_center,transparent_0%,rgba(11,17,33,0.8)_100%)]" />
    </div>
  );
}

