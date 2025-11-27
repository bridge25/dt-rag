/**
 * Constellation Node Component
 *
 * Renders an interactive node in the taxonomy constellation visualization.
 * Features glow effects, hover states, selection, and full accessibility.
 *
 * Design Reference: 뉴디자인2.png
 * @CODE:FRONTEND-REDESIGN-001-NODE
 */

'use client'

import { memo, forwardRef, useCallback } from 'react'
import type { TaxonomyNode } from '@/lib/api/types'

interface Position {
  x: number
  y: number
}

interface ConstellationNodeProps {
  node: TaxonomyNode
  isSelected?: boolean
  isHovered?: boolean
  onClick?: (node: TaxonomyNode) => void
  onHover?: (isHovered: boolean, node: TaxonomyNode) => void
  position: Position
}

const ConstellationNode = forwardRef<HTMLDivElement, ConstellationNodeProps>(
  function ConstellationNode(
    {
      node,
      isSelected = false,
      isHovered = false,
      onClick,
      onHover,
      position
    },
    ref
  ) {
    // Determine node size based on level (root > branch > leaf)
    const getSizeClass = (level: number): string => {
      switch (level) {
        case 1:
          return 'constellation-node-root'
        case 2:
          return 'constellation-node-branch'
        default:
          return 'constellation-node-leaf'
      }
    }

    const sizeClass = getSizeClass(node.level)

    // Build class names
    const baseClasses = [
      'constellation-node',
      sizeClass,
      'rounded-full',
      'flex items-center justify-center',
      'cursor-pointer',
      'transition-all duration-300',
      'relative',
      'backdrop-blur-lg',
      'border border-white/20',
      'bg-gradient-to-br from-white/20 to-white/5',
      'z-10'
    ]

    if (isSelected) {
      baseClasses.push('selected', 'border-cyan-400', 'ring-2', 'ring-cyan-400/50')
    }

    if (isHovered) {
      baseClasses.push('hovered', 'glow-pulse')
    }

    const handleClick = useCallback(() => {
      onClick?.(node)
    }, [node, onClick])

    const handleMouseEnter = useCallback(() => {
      onHover?.(true, node)
    }, [node, onHover])

    const handleMouseLeave = useCallback(() => {
      onHover?.(false, node)
    }, [node, onHover])

    const handleKeyDown = useCallback(
      (e: React.KeyboardEvent<HTMLDivElement>) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick?.(node)
        }
      },
      [node, onClick]
    )

    // Determine size dimensions based on level
    const getSizeDimensions = (level: number): string => {
      switch (level) {
        case 1:
          return 'w-20 h-20'
        case 2:
          return 'w-16 h-16'
        default:
          return 'w-12 h-12'
      }
    }

    const sizeStyles = getSizeDimensions(node.level)

    // Build aria-label with comprehensive information
    const ariaLabel = `${node.name}, Level ${node.level}, ${node.document_count ?? 0} documents`

    return (
      <div
        ref={ref}
        role="button"
        tabIndex={0}
        aria-label={ariaLabel}
        aria-selected={isSelected}
        className={`${baseClasses.join(' ')} ${sizeStyles}`}
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
          position: 'absolute'
        }}
        onClick={handleClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onKeyDown={handleKeyDown}
      >
        {/* Node Content */}
        <div className="flex flex-col items-center justify-center gap-1 text-center px-2 py-1">
          {/* Node Label */}
          <div className="text-xs font-semibold text-white truncate max-w-full" title={node.name}>
            {node.name}
          </div>

          {/* Document Count - Only shown on larger nodes */}
          {node.level <= 2 && node.document_count !== undefined && (
            <div
              className="text-xs text-cyan-300/70"
              aria-label={`${node.document_count} documents`}
            >
              {node.document_count}
            </div>
          )}
        </div>
      </div>
    )
  }
)

export default memo(ConstellationNode)
