'use client'

import React, { memo, useCallback, CSSProperties } from 'react'
import { motion } from 'framer-motion'
import {
  ChevronRight,
  ChevronDown,
  FileText,
  Folder,
  FolderOpen,
  Hash,
  TrendingUp
} from 'lucide-react'
import { TaxonomyNode } from '@/types/taxonomy'
import { cn } from '@/lib/utils'

interface TreeNodeProps {
  node: TaxonomyNode & { level: number; hasChildren: boolean; index: number }
  level: number
  expanded: boolean
  hasChildren: boolean
  selected: boolean
  focused: boolean
  onToggle: (nodeId: string) => void
  onSelect: (nodeId: string) => void
  compactMode?: boolean
  style?: CSSProperties

  // Accessibility props
  role?: string
  ariaExpanded?: boolean
  ariaLevel?: number
  ariaSelected?: boolean
  ariaSetSize?: number
  ariaPosInSet?: number
}

const TreeNodeComponent = ({
  node,
  level,
  expanded,
  hasChildren,
  selected,
  focused,
  onToggle,
  onSelect,
  compactMode = false,
  style,
  role = "treeitem",
  ariaExpanded,
  ariaLevel,
  ariaSelected,
  ariaSetSize,
  ariaPosInSet
}: TreeNodeProps) => {
  const handleClick = useCallback((event: React.MouseEvent) => {
    event.preventDefault()
    event.stopPropagation()

    if (hasChildren && event.detail === 2) {
      // Double-click to toggle
      onToggle(node.node_id)
    } else {
      onSelect(node.node_id)
    }
  }, [hasChildren, onToggle, onSelect, node.node_id])

  const handleToggleClick = useCallback((event: React.MouseEvent) => {
    event.preventDefault()
    event.stopPropagation()
    if (hasChildren) {
      onToggle(node.node_id)
    }
  }, [hasChildren, onToggle, node.node_id])

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      if (hasChildren) {
        onToggle(node.node_id)
      }
      onSelect(node.node_id)
    }
  }, [hasChildren, onToggle, onSelect, node.node_id])

  const indentSize = compactMode ? 16 : 20
  const paddingLeft = level * indentSize + (compactMode ? 8 : 12)

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getNodeIcon = () => {
    if (hasChildren) {
      return expanded ? <FolderOpen className="h-4 w-4" /> : <Folder className="h-4 w-4" />
    }
    return <FileText className="h-4 w-4" />
  }

  const formatDocumentCount = (count?: number) => {
    if (count === undefined || count === 0) return ''
    if (count >= 1000) {
      return `(${(count / 1000).toFixed(1)}k)`
    }
    return `(${count})`
  }

  return (
    <motion.div
      style={style}
      className={cn(
        "flex items-center cursor-pointer transition-colors relative group",
        "border-l-2 border-transparent",
        selected && "bg-primary/10 border-l-primary",
        focused && "ring-2 ring-primary ring-inset",
        !selected && "hover:bg-accent/50",
        compactMode ? "h-7" : "h-9"
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={focused ? 0 : -1}
      role={role}
      aria-expanded={ariaExpanded}
      aria-level={ariaLevel}
      aria-selected={ariaSelected}
      aria-setsize={ariaSetSize}
      aria-posinset={ariaPosInSet}
      aria-label={`${node.label}, level ${level + 1}${hasChildren ? `, ${expanded ? 'expanded' : 'collapsed'}` : ''}`}
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.15, delay: node.index * 0.01 }}
    >
      {/* Indentation and expand/collapse button */}
      <div
        className="flex items-center flex-shrink-0"
        style={{ paddingLeft }}
      >
        {hasChildren ? (
          <button
            onClick={handleToggleClick}
            className="p-1 rounded hover:bg-accent transition-colors"
            aria-label={expanded ? 'Collapse' : 'Expand'}
            tabIndex={-1}
          >
            <motion.div
              animate={{ rotate: expanded ? 90 : 0 }}
              transition={{ duration: 0.15 }}
            >
              <ChevronRight className={cn("h-3 w-3", compactMode ? "h-2.5 w-2.5" : "h-3 w-3")} />
            </motion.div>
          </button>
        ) : (
          <div className={cn("w-5 h-5", compactMode && "w-4 h-4")} />
        )}
      </div>

      {/* Node icon */}
      <div className="flex-shrink-0 mr-2 text-muted-foreground">
        {getNodeIcon()}
      </div>

      {/* Node content */}
      <div className="flex-1 min-w-0 flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <span className={cn(
              "truncate font-medium",
              compactMode ? "text-sm" : "text-base",
              selected ? "text-primary" : "text-foreground"
            )}>
              {node.label}
            </span>

            {/* Document count */}
            {node.document_count !== undefined && node.document_count > 0 && (
              <span className={cn(
                "text-muted-foreground font-mono",
                compactMode ? "text-xs" : "text-sm"
              )}>
                {formatDocumentCount(node.document_count)}
              </span>
            )}
          </div>

          {/* Path breadcrumb for search results */}
          {!compactMode && node.canonical_path.length > 1 && (
            <div className="text-xs text-muted-foreground truncate mt-0.5">
              {node.canonical_path.slice(0, -1).join(' → ')}
            </div>
          )}
        </div>

        {/* Confidence indicator */}
        <div className="flex-shrink-0 flex items-center space-x-1 ml-2">
          {node.confidence < 1.0 && (
            <div className="flex items-center space-x-1">
              <TrendingUp className={cn(
                "h-3 w-3",
                getConfidenceColor(node.confidence),
                compactMode && "h-2.5 w-2.5"
              )} />
              <span className={cn(
                "font-mono",
                getConfidenceColor(node.confidence),
                compactMode ? "text-xs" : "text-sm"
              )}>
                {(node.confidence * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Hover actions */}
      <div className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity ml-2">
        <button
          onClick={(e) => {
            e.stopPropagation()
            // TODO: Implement node actions (edit, delete, etc.)
          }}
          className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
          aria-label="Node actions"
          tabIndex={-1}
        >
          <Hash className="h-3 w-3" />
        </button>
      </div>

      {/* Focus indicator */}
      {focused && (
        <div className="absolute inset-0 border-2 border-primary rounded pointer-events-none" />
      )}
    </motion.div>
  )
}

export const TreeNode = memo(TreeNodeComponent)