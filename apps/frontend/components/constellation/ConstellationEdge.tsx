/**
 * Constellation Edge Component
 *
 * Animated energy beam connecting constellation nodes with gradient and glow effects.
 *
 * Design Reference: 뉴디자인2.png - Energy beams between nodes
 * @CODE:FRONTEND-REDESIGN-001-EDGE
 */

"use client"

import { memo, useMemo } from "react"

interface Position {
  x: number
  y: number
}

interface ConstellationEdgeProps {
  source: Position
  target: Position
  isActive?: boolean
  strength?: number // 0-1
  edgeId: string
}

const ConstellationEdge = memo(function ConstellationEdge({
  source,
  target,
  isActive = true,
  strength = 0.5,
  edgeId
}: ConstellationEdgeProps) {
  // Calculate opacity based on strength
  const opacity = useMemo(() => {
    if (strength === undefined) return 0.6
    return 0.3 + strength * 0.7 // Range from 0.3 to 1.0
  }, [strength])

  // Calculate gradient stop opacity
  const gradientOpacity = useMemo(() => {
    if (strength === undefined) return 0.4
    return 0.2 + strength * 0.8 // Range from 0.2 to 1.0
  }, [strength])

  // CSS classes
  const baseClasses = [
    "constellation-edge",
    "transition-all duration-300"
  ]

  if (isActive) {
    baseClasses.push("constellation-edge-active", "energy-beam")
  }

  const classString = baseClasses.join(" ")

  return (
    <>
      <defs>
        <linearGradient id={`gradient-${edgeId}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="rgba(56, 189, 248, 0.3)" stopOpacity={gradientOpacity} />
          <stop offset="50%" stopColor="rgba(0, 247, 255, 0.6)" stopOpacity={gradientOpacity * 1.2} />
          <stop offset="100%" stopColor="rgba(56, 189, 248, 0.3)" stopOpacity={gradientOpacity} />
        </linearGradient>

        {/* Glow filter for active edges */}
        {isActive && (
          <filter id={`glow-${edgeId}`}>
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        )}
      </defs>

      {/* Connection Line */}
      <line
        data-testid="constellation-edge-line"
        className={classString}
        x1={source.x}
        y1={source.y}
        x2={target.x}
        y2={target.y}
        stroke={`url(#gradient-${edgeId})`}
        strokeWidth={isActive ? 2.5 : 2}
        opacity={opacity}
        filter={isActive ? `url(#glow-${edgeId})` : undefined}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={!isActive ? "5,5" : undefined}
        vectorEffect="non-scaling-stroke"
      />
    </>
  )
})

export default ConstellationEdge
