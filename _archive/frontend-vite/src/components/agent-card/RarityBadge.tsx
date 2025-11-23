/**
 * RarityBadge Component
 *
 * @CODE:AGENT-CARD-001
 */
import { memo } from 'react'
import { cn } from '@/lib/utils'
import type { Rarity } from '@/lib/api/types'

interface RarityBadgeProps {
  rarity: Rarity
  className?: string
}

export const RarityBadge = memo<RarityBadgeProps>(function RarityBadge({ rarity, className }) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide',
        // Tailwind v4 JIT requires explicit class names
        rarity.toLowerCase() === 'common' && 'bg-gray-500 text-white',
        rarity.toLowerCase() === 'rare' && 'bg-blue-500 text-white',
        rarity.toLowerCase() === 'epic' && 'bg-purple-600 text-white',
        rarity.toLowerCase() === 'legendary' && 'bg-accent-gold-500 text-black',
        className
      )}
      aria-label={`Rarity: ${rarity}`}
    >
      {rarity}
    </span>
  )
})
