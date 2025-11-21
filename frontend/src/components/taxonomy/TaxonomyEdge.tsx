/**
 * Custom Taxonomy Edge Component - visualizes hierarchical relationships
 *
 * @CODE:TAXONOMY-VIZ-001
 */

import { memo } from 'react'
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from '@xyflow/react'

function TaxonomyEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  selected,
  animated,
  source,
  target,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  const strokeColor = selected ? '#3b82f6' : '#b1b1b7'

  return (
    <>
      <g aria-label={`Edge from ${source} to ${target}`}>
        <BaseEdge
          id={id}
          path={edgePath}
          style={{
            stroke: strokeColor,
            strokeWidth: 2,
            strokeLinecap: 'round',
          }}
          markerEnd="url(#arrow)"
          className={animated ? 'animated' : ''}
        />
      </g>
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: 'all',
          }}
          className="nodrag nopan"
        />
      </EdgeLabelRenderer>

      <defs>
        <marker
          id="arrow"
          viewBox="0 0 10 10"
          refX="5"
          refY="5"
          markerWidth="6"
          markerHeight="6"
          orient="auto-start-reverse"
        >
          <path
            d="M 0 0 L 10 5 L 0 10 z"
            fill={strokeColor}
          />
        </marker>
      </defs>
    </>
  )
}

export default memo(TaxonomyEdge)
