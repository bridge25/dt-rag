// @CODE:AGENT-CARD-001-UI-004
import { memo } from 'react'
import { cn } from '@/lib/utils'

interface ActionButtonsProps {
  onView: () => void
  onDelete: () => void
  agentName?: string
  className?: string
}

export const ActionButtons = memo<ActionButtonsProps>(function ActionButtons({ onView, onDelete, agentName, className }) {
  const viewLabel = agentName ? `View ${agentName} details` : 'View agent details'
  const deleteLabel = agentName ? `Delete ${agentName}` : 'Delete agent'

  return (
    <div className={cn('flex gap-2', className)}>
      <button
        onClick={onView}
        aria-label={viewLabel}
        className="flex-1 px-3 py-1.5 bg-primary text-white text-sm font-medium rounded hover:opacity-90 transition-opacity"
      >
        View
      </button>
      <button
        onClick={onDelete}
        aria-label={deleteLabel}
        className="flex-1 px-3 py-1.5 bg-red-500 text-white text-sm font-medium rounded hover:opacity-90 transition-opacity"
      >
        Delete
      </button>
    </div>
  )
})
