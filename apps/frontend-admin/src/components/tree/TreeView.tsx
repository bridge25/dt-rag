'use client'

import React, { useState, useMemo, useCallback } from 'react'
import { FixedSizeList as List } from 'react-window'
import { TreeNode } from './TreeNode'
import { VersionDropdown } from './VersionDropdown'
import type { TaxonomyTree, TaxonomyNode } from '@/types/common'

interface TreeViewProps {
  tree: TaxonomyTree | null
  versions: string[]
  currentVersion: string
  onVersionChange: (version: string) => void
  loading?: boolean
  hideVersionDropdown?: boolean
  sidebarMode?: boolean
}

interface FlatNode extends TaxonomyNode {
  level: number
  hasChildren: boolean
}

export function TreeView({
  tree,
  versions,
  currentVersion,
  onVersionChange,
  loading = false,
  hideVersionDropdown = false,
  sidebarMode = false
}: TreeViewProps) {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(sidebarMode ? ['treeview'] : []))
  const [selectedNode, setSelectedNode] = useState<string | null>(null)

  // 트리를 평면 구조로 변환 (가상 스크롤용)
  const flatNodes = useMemo(() => {
    if (!tree) return []
    
    const nodeMap = new Map<string, TaxonomyNode>()
    const childrenMap = new Map<string, string[]>()
    
    // 노드 맵 생성
    tree.nodes.forEach(node => {
      nodeMap.set(node.node_id, node)
    })
    
    // 부모-자식 관계 맵 생성
    tree.edges.forEach(edge => {
      if (!childrenMap.has(edge.parent)) {
        childrenMap.set(edge.parent, [])
      }
      childrenMap.get(edge.parent)!.push(edge.child)
    })
    
    // 루트 노드들 찾기 (부모가 없는 노드들)
    const rootNodes = tree.nodes.filter(node => 
      !tree.edges.some(edge => edge.child === node.node_id)
    )
    
    // 재귀적으로 평면 구조 생성
    const flattenTree = (nodeId: string, level: number): FlatNode[] => {
      const node = nodeMap.get(nodeId)
      if (!node) return []
      
      const children = childrenMap.get(nodeId) || []
      const hasChildren = children.length > 0
      const isExpanded = expandedNodes.has(nodeId)
      
      const result: FlatNode[] = [{
        ...node,
        level,
        hasChildren
      }]
      
      // 확장된 노드의 자식들만 포함
      if (isExpanded && hasChildren) {
        children.forEach(childId => {
          result.push(...flattenTree(childId, level + 1))
        })
      }
      
      return result
    }
    
    return rootNodes.flatMap(node => flattenTree(node.node_id, 0))
  }, [tree, expandedNodes])

  const handleToggle = useCallback((nodeId: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev)
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId)
      } else {
        newSet.add(nodeId)
      }
      return newSet
    })
  }, [])

  const handleSelect = useCallback((nodeId: string) => {
    setSelectedNode(nodeId)
  }, [])

  // 가상 스크롤 아이템 렌더러
  const ItemRenderer = useCallback(({ index, style }: { index: number; style: React.CSSProperties }) => {
    const node = flatNodes[index]
    if (!node) return null
    
    return (
      <TreeNode
        key={node.node_id}
        node={node}
        level={node.level}
        expanded={expandedNodes.has(node.node_id)}
        hasChildren={node.hasChildren}
        selected={selectedNode === node.node_id}
        onToggle={handleToggle}
        onSelect={handleSelect}
        style={style}
        sidebarMode={sidebarMode}
      />
    )
  }, [flatNodes, expandedNodes, selectedNode, handleToggle, handleSelect, sidebarMode])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">트리 데이터를 로딩 중...</span>
      </div>
    )
  }

  if (!tree) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">트리 데이터가 없습니다.</p>
      </div>
    )
  }

  if (sidebarMode) {
    return (
      <div className="h-full">
        {/* TreeView 라벨 */}
        <div className="p-3 border-b border-gray-200 bg-gray-50">
          <button 
            className="flex items-center w-full text-left hover:bg-gray-100 rounded px-2 py-1 transition-colors"
            onClick={() => setExpandedNodes(prev => new Set(prev.has('treeview') ? [] : ['treeview']))}
          >
            <span className="text-xs mr-2 text-gray-600">
              {expandedNodes.has('treeview') ? '▼' : '▶'}
            </span>
            <span className="text-sm font-semibold text-gray-800 uppercase tracking-wide">TreeView</span>
          </button>
        </div>

        {/* 가상 스크롤 트리 - 사이드바 모드 */}
        {expandedNodes.has('treeview') && (
          <div className="flex-1">
            <List
              height={600} // 사이드바 높이
              itemCount={flatNodes.length}
              itemSize={32} // 컴팩트한 높이
              className="react-window-list"
            >
              {ItemRenderer}
            </List>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={hideVersionDropdown ? "p-6" : "bg-white rounded-lg shadow-sm border p-6"}>
      {/* 버전 선택 - 숨김 옵션 */}
      {!hideVersionDropdown && (
        <VersionDropdown
          versions={versions}
          currentVersion={currentVersion}
          onVersionChange={onVersionChange}
          loading={loading}
        />
      )}

      {/* 트리 통계 - 간소화 또는 숨김 */}
      {!hideVersionDropdown && (
        <div className="mb-4 p-3 bg-gray-50 rounded-md">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>총 {tree.total_nodes}개 노드</span>
            <span>총 {tree.total_documents}개 문서</span>
            <span>표시 중: {flatNodes.length}개 노드</span>
          </div>
        </div>
      )}

      {/* 가상 스크롤 트리 */}
      <div className={hideVersionDropdown ? "" : "border border-gray-200 rounded-md"}>
        <List
          height={500} // 높이 조정
          itemCount={flatNodes.length}
          itemSize={70} // 노드 높이 증가 (더 여유롭게)
          className="react-window-list"
        >
          {ItemRenderer}
        </List>
      </div>

      {/* 선택된 노드 정보 - 숨김 (이미지와 일치) */}
      {!hideVersionDropdown && selectedNode && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <h4 className="text-sm font-medium text-blue-900 mb-1">선택된 노드</h4>
          {(() => {
            const selected = flatNodes.find(n => n.node_id === selectedNode)
            return selected ? (
              <div className="text-sm text-blue-800">
                <p><strong>라벨:</strong> {selected.label}</p>
                <p><strong>경로:</strong> {selected.canonical_path.join(' > ')}</p>
                <p><strong>신뢰도:</strong> {(selected.confidence * 100).toFixed(1)}%</p>
                {selected.document_count !== undefined && (
                  <p><strong>문서 수:</strong> {selected.document_count}개</p>
                )}
              </div>
            ) : null
          })()}
        </div>
      )}
    </div>
  )
}