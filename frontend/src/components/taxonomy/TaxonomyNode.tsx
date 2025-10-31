// @CODE:TAXONOMY-VIZ-001-004
// @CODE:TAXONOMY-VIZ-001-016
// Custom Taxonomy Node Component - displays name, level, and document count
// Accessibility: role, tab index, ARIA labels, screen reader support

import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import type { TaxonomyNode as TaxonomyNodeData } from '../../lib/api/types'

interface TaxonomyNodeProps extends NodeProps {
  data: {
    taxonomyNode: TaxonomyNodeData
    isExpanded: boolean
  }
}

function TaxonomyNode({ data, selected }: TaxonomyNodeProps) {
  const { taxonomyNode } = data
  const documentCount = taxonomyNode.document_count ?? 0
  const hasChildren = taxonomyNode.children && taxonomyNode.children.length > 0

  return (
    <div
      role="button"
      tabIndex={0}
      className={`
        min-w-[150px] rounded-lg border-2 bg-white px-4 py-3 shadow-md
        transition-all duration-200 hover:shadow-lg
        ${selected ? 'ring-2 ring-blue-500 border-blue-400' : 'border-gray-300'}
      `}
      aria-label={`Taxonomy node: ${taxonomyNode.name}, Level ${taxonomyNode.level}, ${documentCount} documents`}
      aria-selected={selected}
    >
      <Handle type="target" position={Position.Top} />

      <div className="flex flex-col gap-2">
        {/* Node Name */}
        <div className="truncate text-sm font-semibold text-gray-900" title={taxonomyNode.name}>
          {taxonomyNode.name}
        </div>

        {/* Level Badge */}
        <div className="flex items-center gap-2 text-xs text-gray-600">
          <span className="rounded bg-gray-100 px-2 py-0.5 font-medium">
            Level {taxonomyNode.level}
          </span>

          {/* Document Count */}
          <span className="flex items-center gap-1" aria-label={`${documentCount} documents`}>
            <svg
              className="h-3 w-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            {documentCount}
          </span>
        </div>

        {/* Children Indicator */}
        {hasChildren && (
          <div
            data-testid="children-indicator"
            className="mt-1 flex items-center gap-1 text-xs text-gray-500"
            aria-label={`${taxonomyNode.children?.length} subcategories`}
          >
            <svg
              className="h-3 w-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
            {taxonomyNode.children?.length} subcategories
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

export default memo(TaxonomyNode)
