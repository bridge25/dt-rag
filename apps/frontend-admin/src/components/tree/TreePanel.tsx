'use client'

import { useMemo } from 'react'
import { Tree } from 'react-arborist'
import { TaxonomyNode } from '@/services/taxonomyService'

interface TreeData {
  id: string
  name: string
  children?: TreeData[]
}

interface TreePanelProps {
  nodes: TaxonomyNode[]
  onNodeSelect?: (node: TaxonomyNode) => void
  className?: string
}

export default function TreePanel({ nodes, onNodeSelect, className = '' }: TreePanelProps) {
  const treeData = useMemo(() => {
    const buildTreeData = (flatNodes: TaxonomyNode[]): TreeData[] => {
      const nodeMap = new Map<string, TreeData>()
      const rootNodes: TreeData[] = []

      flatNodes.forEach(node => {
        nodeMap.set(node.node_id, {
          id: node.node_id,
          name: node.label,
          children: []
        })
      })

      flatNodes.forEach(node => {
        const treeNode = nodeMap.get(node.node_id)
        if (!treeNode) {
          console.warn(`TreePanel: Node ${node.node_id} not found in nodeMap`)
          return
        }

        const path = node.canonical_path

        if (path.length === 1) {
          rootNodes.push(treeNode)
        } else {
          const parentNode = flatNodes.find(n =>
            n.canonical_path.length === path.length - 1 &&
            n.canonical_path.every((p, i) => p === path[i])
          )

          if (parentNode) {
            const parent = nodeMap.get(parentNode.node_id)
            if (parent) {
              parent.children = parent.children || []
              parent.children.push(treeNode)
            }
          }
        }
      })

      return rootNodes
    }

    return buildTreeData(nodes)
  }, [nodes])

  if (nodes.length === 0) {
    return (
      <div className={`flex items-center justify-center h-64 text-gray-500 ${className}`}>
        <p>No taxonomy nodes available</p>
      </div>
    )
  }

  return (
    <div className={`h-full ${className}`}>
      <Tree
        data={treeData}
        openByDefault={false}
        width="100%"
        height={600}
        indent={24}
        rowHeight={36}
        overscanCount={10}
      >
        {({ node, style, dragHandle }) => (
          <div
            style={style}
            ref={dragHandle}
            className="flex items-center px-2 hover:bg-gray-100 cursor-pointer rounded"
            onClick={() => {
              const originalNode = nodes.find(n => n.node_id === node.data.id)
              if (originalNode && onNodeSelect) {
                onNodeSelect(originalNode)
              }
            }}
          >
            <span className="flex items-center">
              {node.isLeaf ? (
                <span className="w-4 h-4 mr-2 text-gray-400">📄</span>
              ) : (
                <span className="w-4 h-4 mr-2">
                  {node.isOpen ? '📂' : '📁'}
                </span>
              )}
              <span className="text-sm font-medium text-gray-800">
                {node.data.name}
              </span>
            </span>
          </div>
        )}
      </Tree>
    </div>
  )
}
