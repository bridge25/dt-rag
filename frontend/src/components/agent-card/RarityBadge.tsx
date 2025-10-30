// @CODE:AGENT-CARD-001-UI-001
import { memo } from 'react'
import { cn } from '@/lib/utils'
import type { Rarity } from '@/lib/api/types'

interface RarityBadgeProps {
  rarity: Rarity
  className?: string
}

const rarityStyles: Record<Rarity, string> = {
  Common: 'bg-gray-500 text-white',
  Rare: 'bg-blue-500 text-white',
  Epic: 'bg-purple-600 text-white',
  Legendary: 'bg-accent-gold text-black',
}

export const RarityBadge = memo<RarityBadgeProps>(function RarityBadge({ rarity, className }) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide',
        rarityStyles[rarity],
        className
      )}
      aria-label={`Rarity: ${rarity}`}
    >
      {rarity}
    </span>
  )
})
