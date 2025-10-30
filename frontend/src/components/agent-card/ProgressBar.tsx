// @CODE:AGENT-CARD-001-UI-002
import { memo } from 'react'
import { cn } from '@/lib/utils'

interface ProgressBarProps {
  current: number
  max: number
  label?: string
  ariaLabel?: string
  className?: string
}

export const ProgressBar = memo<ProgressBarProps>(function ProgressBar({
  current,
  max,
  label,
  ariaLabel = 'Progress',
  className,
}) {
  const percentage = max > 0 ? Math.min((current / max) * 100, 100) : 0

  return (
    <div className={cn('w-full', className)}>
      <div
        role="progressbar"
        aria-valuenow={current}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={ariaLabel}
        className="relative h-2 w-full bg-gray-200 rounded-full overflow-hidden"
      >
        <div
          className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 transition-all duration-300 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
      {label && (
        <p className="text-xs text-gray-600 mt-1 text-center">{label}</p>
      )}
    </div>
  )
})
