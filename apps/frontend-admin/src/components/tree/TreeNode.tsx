'use client'

import React, { memo } from 'react'
import { ChevronRight, ChevronDown, File, Folder, FolderOpen } from 'lucide-react'
import { clsx } from 'clsx'
import type { TaxonomyNode } from '@/types/common'

interface TreeNodeProps {
  node: TaxonomyNode
  level: number
  expanded: boolean
  hasChildren: boolean
  selected: boolean
  focused?: boolean
  onToggle: (nodeId: string) => void
  onSelect: (nodeId: string) => void
  style?: React.CSSProperties
  sidebarMode?: boolean
  // 접근성 속성
  role?: string
  ariaExpanded?: boolean
  ariaLevel?: number
  ariaSelected?: boolean
  ariaSetSize?: number
  ariaPosInSet?: number
}

export const TreeNode = memo<TreeNodeProps>(function TreeNode({
  node,
  level,
  expanded,
  hasChildren,
  selected,
  focused = false,
  onToggle,
  onSelect,
  style,
  sidebarMode = false,
  role = 'treeitem',
  ariaExpanded,
  ariaLevel,
  ariaSelected,
  ariaSetSize,
  ariaPosInSet
}) {
  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (hasChildren) {
      onToggle(node.node_id)
    }
  }

  const handleSelect = () => {
    onSelect(node.node_id)
  }

  // 성능 최적화: 깊이별 인덴테이션 계산
  const indentWidth = sidebarMode ? level * 16 : level * 24

  if (sidebarMode) {
    return (
      <div
        style={style}
        className={clsx(
          'flex items-center py-1.5 px-2 hover:bg-gray-200 cursor-pointer transition-colors text-xs',
          selected && 'bg-blue-100 border-l-2 border-l-blue-500 font-medium',
          focused && 'ring-2 ring-blue-500 ring-opacity-50'
        )}
        onClick={handleSelect}
        role={role}
        aria-expanded={ariaExpanded}
        aria-level={ariaLevel}
        aria-selected={ariaSelected}
        aria-setsize={ariaSetSize}
        aria-posinset={ariaPosInSet}
        aria-label={`${node.label}, 레벨 ${level + 1}${hasChildren ? (expanded ? ', 확장됨' : ', 축소됨') : ''}`}
        tabIndex={focused ? 0 : -1}
      >
        {/* 인덴테이션 */}
        <div style={{ width: indentWidth }} className="shrink-0" />
        
        {/* 확장/축소 표시 */}
        {hasChildren ? (
          <button
            onClick={handleToggle}
            className="mr-2 text-gray-500 hover:text-gray-700 shrink-0 w-3 h-3 flex items-center justify-center"
            aria-label={expanded ? '축소' : '확장'}
            aria-expanded={expanded}
          >
            <span className="text-xs leading-none" aria-hidden="true">
              {expanded ? '▼' : '▶'}
            </span>
          </button>
        ) : (
          <div className="w-3 h-3 mr-2 shrink-0" aria-hidden="true" />
        )}
        
        {/* 노드 라벨 */}
        <span className={clsx(
          'truncate text-gray-700 leading-relaxed',
          selected && 'text-blue-800 font-medium'
        )}>
          {node.label}
        </span>
      </div>
    )
  }

  return (
    <div
      style={style}
      className={clsx(
        'tree-node-container flex items-center py-3 px-4 hover:bg-gray-50 cursor-pointer transition-colors',
        selected && 'bg-blue-50 border-l-4 border-l-blue-500',
        focused && 'ring-2 ring-blue-500 ring-opacity-50'
      )}
      onClick={handleSelect}
      role={role}
      aria-expanded={ariaExpanded}
      aria-level={ariaLevel}
      aria-selected={ariaSelected}
      aria-setsize={ariaSetSize}
      aria-posinset={ariaPosInSet}
      aria-label={`${node.label}, 레벨 ${level + 1}${hasChildren ? (expanded ? ', 확장됨' : ', 축소됨') : ''}`}
      tabIndex={focused ? 0 : -1}
    >
      {/* 인덴테이션 */}
      <div style={{ width: indentWidth }} className="shrink-0" />
      
      {/* 확장/축소 버튼 */}
      <button
        onClick={handleToggle}
        className={clsx(
          'p-1.5 hover:bg-gray-200 rounded transition-colors mr-3 shrink-0',
          !hasChildren && 'invisible'
        )}
        disabled={!hasChildren}
        aria-label={hasChildren ? (expanded ? '축소' : '확장') : undefined}
        aria-expanded={hasChildren ? expanded : undefined}
      >
        {hasChildren && (
          expanded ?
            <ChevronDown className="h-4 w-4 text-gray-600" aria-hidden="true" /> :
            <ChevronRight className="h-4 w-4 text-gray-600" aria-hidden="true" />
        )}
      </button>

      {/* 폴더/파일 아이콘 */}
      <div className="mr-4 shrink-0" aria-hidden="true">
        {hasChildren ? (
          expanded ?
            <FolderOpen className="h-4 w-4 text-blue-500" /> :
            <Folder className="h-4 w-4 text-blue-500" />
        ) : (
          <File className="h-4 w-4 text-gray-400" />
        )}
      </div>

      {/* 노드 정보 */}
      <div className="flex-1 min-w-0">
        <span className="tree-node-label text-sm text-gray-900 leading-5">
          {node.label}
        </span>
        
        {/* 하단: 경로 표시 - 선택된 노드에만 */}
        {selected && (
          <div className="tree-node-path text-xs text-gray-500 leading-4 mt-1">
            {node.canonical_path.join(' › ')}
          </div>
        )}
      </div>
    </div>
  )
})