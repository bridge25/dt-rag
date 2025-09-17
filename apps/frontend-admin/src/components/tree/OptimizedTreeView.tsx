'use client'

import React, {
  useState,
  useMemo,
  useCallback,
  useRef,
  useEffect,
  KeyboardEvent,
  FocusEvent
} from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
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
  index: number
  isVisible: boolean
}

// 메모리 최적화를 위한 WeakMap 캐시
const nodeCache = new WeakMap<TaxonomyNode, FlatNode>()

export function OptimizedTreeView({
  tree,
  versions,
  currentVersion,
  onVersionChange,
  loading = false,
  hideVersionDropdown = false,
  sidebarMode = false
}: TreeViewProps) {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(
    new Set(sidebarMode ? ['treeview'] : [])
  )
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [focusedIndex, setFocusedIndex] = useState<number>(0)

  const parentRef = useRef<HTMLDivElement>(null)
  const treeRef = useRef<HTMLDivElement>(null)

  // 메모리 최적화된 평면 구조 변환
  const flatNodes = useMemo(() => {
    if (!tree) return []

    const nodeMap = new Map<string, TaxonomyNode>()
    const childrenMap = new Map<string, string[]>()

    // 노드 맵 생성 (메모리 효율적)
    tree.nodes.forEach(node => {
      nodeMap.set(node.node_id, node)
    })

    // 부모-자식 관계 맵 생성
    tree.edges.forEach(edge => {
      const children = childrenMap.get(edge.parent) || []
      children.push(edge.child)
      childrenMap.set(edge.parent, children)
    })

    // 루트 노드들 찾기
    const rootNodes = tree.nodes.filter(node =>
      !tree.edges.some(edge => edge.child === node.node_id)
    )

    let globalIndex = 0

    // 캐시를 활용한 재귀적 평면 구조 생성
    const flattenTree = (nodeId: string, level: number): FlatNode[] => {
      const node = nodeMap.get(nodeId)
      if (!node) return []

      // 캐시 확인
      let flatNode = nodeCache.get(node)
      if (!flatNode) {
        const children = childrenMap.get(nodeId) || []
        flatNode = {
          ...node,
          level,
          hasChildren: children.length > 0,
          index: globalIndex++,
          isVisible: true
        }
        nodeCache.set(node, flatNode)
      } else {
        // 인덱스와 레벨 업데이트
        flatNode.index = globalIndex++
        flatNode.level = level
      }

      const isExpanded = expandedNodes.has(nodeId)
      const result: FlatNode[] = [flatNode]

      // 확장된 노드의 자식들만 포함
      if (isExpanded && flatNode.hasChildren) {
        const children = childrenMap.get(nodeId) || []
        children.forEach(childId => {
          result.push(...flattenTree(childId, level + 1))
        })
      }

      return result
    }

    globalIndex = 0 // 인덱스 리셋
    return rootNodes.flatMap(node => flattenTree(node.node_id, 0))
  }, [tree, expandedNodes])

  // TanStack Virtual 설정
  const virtualizer = useVirtualizer({
    count: flatNodes.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => sidebarMode ? 32 : 70,
    overscan: 10, // 성능 최적화: 화면 밖 렌더링 최소화
    // 동적 크기 지원
    measureElement: (element) => {
      return element?.getBoundingClientRect().height ?? (sidebarMode ? 32 : 70)
    }
  })

  // 메모화된 토글 핸들러
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

  // 메모화된 선택 핸들러
  const handleSelect = useCallback((nodeId: string, index: number) => {
    setSelectedNode(nodeId)
    setFocusedIndex(index)
  }, [])

  // WCAG 2.1 AAA 접근성: 키보드 네비게이션
  const handleKeyDown = useCallback((event: KeyboardEvent<HTMLDivElement>) => {
    const { key } = event

    switch (key) {
      case 'ArrowDown':
        event.preventDefault()
        setFocusedIndex(prev => Math.min(prev + 1, flatNodes.length - 1))
        break

      case 'ArrowUp':
        event.preventDefault()
        setFocusedIndex(prev => Math.max(prev - 1, 0))
        break

      case 'ArrowRight':
        event.preventDefault()
        const currentNode = flatNodes[focusedIndex]
        if (currentNode?.hasChildren && !expandedNodes.has(currentNode.node_id)) {
          handleToggle(currentNode.node_id)
        } else if (focusedIndex < flatNodes.length - 1) {
          setFocusedIndex(prev => prev + 1)
        }
        break

      case 'ArrowLeft':
        event.preventDefault()
        const focusedNode = flatNodes[focusedIndex]
        if (focusedNode?.hasChildren && expandedNodes.has(focusedNode.node_id)) {
          handleToggle(focusedNode.node_id)
        } else if (focusedNode?.level > 0) {
          // 부모 노드로 이동
          const parentIndex = flatNodes.findIndex(node =>
            node.level === focusedNode.level - 1 &&
            node.index < focusedNode.index
          )
          if (parentIndex !== -1) {
            setFocusedIndex(parentIndex)
          }
        }
        break

      case 'Enter':
      case ' ':
        event.preventDefault()
        const activeNode = flatNodes[focusedIndex]
        if (activeNode) {
          if (activeNode.hasChildren) {
            handleToggle(activeNode.node_id)
          }
          handleSelect(activeNode.node_id, focusedIndex)
        }
        break

      case 'Home':
        event.preventDefault()
        setFocusedIndex(0)
        break

      case 'End':
        event.preventDefault()
        setFocusedIndex(flatNodes.length - 1)
        break
    }
  }, [flatNodes, focusedIndex, expandedNodes, handleToggle, handleSelect])

  // 포커스 관리
  const handleFocus = useCallback((event: FocusEvent<HTMLDivElement>) => {
    if (!flatNodes[focusedIndex]) {
      setFocusedIndex(0)
    }
  }, [flatNodes, focusedIndex])

  // 자동 스크롤 (포커스된 아이템이 보이도록)
  useEffect(() => {
    if (focusedIndex >= 0 && focusedIndex < virtualizer.getVirtualItems().length) {
      virtualizer.scrollToIndex(focusedIndex, { align: 'auto' })
    }
  }, [focusedIndex, virtualizer])

  // 로딩 상태
  if (loading) {
    return (
      <div
        className="flex items-center justify-center h-64"
        role="status"
        aria-label="트리 데이터 로딩 중"
      >
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">트리 데이터를 로딩 중...</span>
      </div>
    )
  }

  // 빈 상태
  if (!tree) {
    return (
      <div className="text-center py-12" role="status" aria-label="트리 데이터 없음">
        <p className="text-gray-500">트리 데이터가 없습니다.</p>
      </div>
    )
  }

  // 사이드바 모드
  if (sidebarMode) {
    return (
      <div className="h-full">
        {/* TreeView 라벨 */}
        <div className="p-3 border-b border-gray-200 bg-gray-50">
          <button
            className="flex items-center w-full text-left hover:bg-gray-100 rounded px-2 py-1 transition-colors"
            onClick={() => setExpandedNodes(prev => new Set(prev.has('treeview') ? [] : ['treeview']))}
            aria-expanded={expandedNodes.has('treeview')}
            aria-label="TreeView 섹션 토글"
          >
            <span className="text-xs mr-2 text-gray-600" aria-hidden="true">
              {expandedNodes.has('treeview') ? '▼' : '▶'}
            </span>
            <span className="text-sm font-semibold text-gray-800 uppercase tracking-wide">TreeView</span>
          </button>
        </div>

        {/* 가상 스크롤 트리 - 사이드바 모드 */}
        {expandedNodes.has('treeview') && (
          <div
            className="flex-1"
            ref={treeRef}
            role="tree"
            aria-label="분류 체계 트리"
            tabIndex={0}
            onKeyDown={handleKeyDown}
            onFocus={handleFocus}
          >
            <div ref={parentRef} className="h-full overflow-auto">
              <div
                style={{
                  height: `${virtualizer.getTotalSize()}px`,
                  width: '100%',
                  position: 'relative',
                }}
              >
                {virtualizer.getVirtualItems().map((virtualItem) => {
                  const node = flatNodes[virtualItem.index]
                  if (!node) return null

                  return (
                    <TreeNode
                      key={node.node_id}
                      node={node}
                      level={node.level}
                      expanded={expandedNodes.has(node.node_id)}
                      hasChildren={node.hasChildren}
                      selected={selectedNode === node.node_id}
                      focused={focusedIndex === virtualItem.index}
                      onToggle={handleToggle}
                      onSelect={(nodeId) => handleSelect(nodeId, virtualItem.index)}
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: `${virtualItem.size}px`,
                        transform: `translateY(${virtualItem.start}px)`,
                      }}
                      sidebarMode={sidebarMode}
                      // 접근성 속성
                      role="treeitem"
                      ariaExpanded={node.hasChildren ? expandedNodes.has(node.node_id) : undefined}
                      ariaLevel={node.level + 1}
                      ariaSelected={selectedNode === node.node_id}
                      ariaSetSize={flatNodes.length}
                      ariaPosInSet={virtualItem.index + 1}
                    />
                  )
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // 메인 모드
  return (
    <div className={hideVersionDropdown ? "p-6" : "bg-white rounded-lg shadow-sm border p-6"}>
      {/* 버전 선택 */}
      {!hideVersionDropdown && (
        <VersionDropdown
          versions={versions}
          currentVersion={currentVersion}
          onVersionChange={onVersionChange}
          loading={loading}
        />
      )}

      {/* 트리 통계 */}
      {!hideVersionDropdown && (
        <div className="mb-4 p-3 bg-gray-50 rounded-md" role="status" aria-live="polite">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>총 {tree.total_nodes}개 노드</span>
            <span>총 {tree.total_documents}개 문서</span>
            <span>표시 중: {flatNodes.length}개 노드</span>
          </div>
        </div>
      )}

      {/* 가상 스크롤 트리 */}
      <div
        className={hideVersionDropdown ? "" : "border border-gray-200 rounded-md"}
        ref={treeRef}
        role="tree"
        aria-label="분류 체계 트리"
        tabIndex={0}
        onKeyDown={handleKeyDown}
        onFocus={handleFocus}
      >
        <div ref={parentRef} style={{ height: '500px', overflow: 'auto' }}>
          <div
            style={{
              height: `${virtualizer.getTotalSize()}px`,
              width: '100%',
              position: 'relative',
            }}
          >
            {virtualizer.getVirtualItems().map((virtualItem) => {
              const node = flatNodes[virtualItem.index]
              if (!node) return null

              return (
                <TreeNode
                  key={node.node_id}
                  node={node}
                  level={node.level}
                  expanded={expandedNodes.has(node.node_id)}
                  hasChildren={node.hasChildren}
                  selected={selectedNode === node.node_id}
                  focused={focusedIndex === virtualItem.index}
                  onToggle={handleToggle}
                  onSelect={(nodeId) => handleSelect(nodeId, virtualItem.index)}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: `${virtualItem.size}px`,
                    transform: `translateY(${virtualItem.start}px)`,
                  }}
                  sidebarMode={sidebarMode}
                  // 접근성 속성
                  role="treeitem"
                  ariaExpanded={node.hasChildren ? expandedNodes.has(node.node_id) : undefined}
                  ariaLevel={node.level + 1}
                  ariaSelected={selectedNode === node.node_id}
                  ariaSetSize={flatNodes.length}
                  ariaPosInSet={virtualItem.index + 1}
                />
              )
            })}
          </div>
        </div>
      </div>

      {/* 선택된 노드 정보 */}
      {!hideVersionDropdown && selectedNode && (
        <div
          className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md"
          role="status"
          aria-live="polite"
          aria-label="선택된 노드 정보"
        >
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