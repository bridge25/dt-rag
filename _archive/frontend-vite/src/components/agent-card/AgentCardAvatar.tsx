/**
 * AgentCardAvatar Component
 *
 * Displays Pokemon-style avatar for Agent Cards.
 * - Uses Lucide Icons as fallback (12 icons mapped by rarity)
 * - Deterministic icon selection based on agent_id hash
 * - Supports future image URLs (avatar_url)
 *
 * @CODE:AGENT-CARD-001
 */
import { memo } from 'react'
import * as LucideIcons from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Rarity } from '@/lib/api/types'
import { getDefaultAvatarIcon } from '@/lib/api/types'

interface AgentCardAvatarProps {
  agentId: string
  agentName: string
  rarity: Rarity
  avatarUrl?: string | null
  className?: string
}

// Fallback gradients by rarity (Pokemon card style)
const RARITY_GRADIENTS: Record<Rarity, string> = {
  Common: 'from-gray-200 to-gray-300',
  Rare: 'from-blue-200 to-blue-300',
  Epic: 'from-purple-200 to-purple-400',
  Legendary: 'from-accent-gold-300 to-accent-gold-500',
}

// Icon size by rarity (emphasize legendary)
const RARITY_ICON_SIZES: Record<Rarity, string> = {
  Common: 'w-16 h-16',
  Rare: 'w-20 h-20',
  Epic: 'w-24 h-24',
  Legendary: 'w-28 h-28',
}

export const AgentCardAvatar = memo<AgentCardAvatarProps>(function AgentCardAvatar({
  agentId,
  agentName,
  rarity,
  avatarUrl,
  className,
}) {
  // If avatar_url is provided and valid, use image (future enhancement)
  if (avatarUrl) {
    return (
      <div
        className={cn(
          'relative w-full h-48 rounded-lg overflow-hidden',
          'bg-gradient-to-br',
          RARITY_GRADIENTS[rarity],
          className
        )}
        role="img"
        aria-label={`${agentName} avatar`}
      >
        <img
          src={avatarUrl}
          alt={`${agentName} character`}
          className="w-full h-full object-cover"
          loading="lazy"
        />
      </div>
    )
  }

  // Fallback: Lucide Icon based on rarity and agent_id
  const iconName = getDefaultAvatarIcon(rarity, agentId)
  const IconComponent = (LucideIcons as unknown as Record<string, React.ComponentType<{ className?: string }>>)[iconName]

  if (!IconComponent) {
    // Ultimate fallback: User icon
    const FallbackIcon = LucideIcons.User
    return (
      <div
        className={cn(
          'relative w-full h-48 rounded-lg',
          'bg-gradient-to-br',
          RARITY_GRADIENTS[rarity],
          'flex items-center justify-center',
          className
        )}
        role="img"
        aria-label={`${agentName} avatar`}
      >
        <FallbackIcon className="w-20 h-20 text-gray-700/50" />
      </div>
    )
  }

  return (
    <div
      className={cn(
        'relative w-full h-48 rounded-lg',
        'bg-gradient-to-br',
        RARITY_GRADIENTS[rarity],
        'flex items-center justify-center',
        className
      )}
      role="img"
      aria-label={`${agentName} avatar - ${rarity} tier`}
    >
      <IconComponent
        className={cn(
          RARITY_ICON_SIZES[rarity],
          'text-gray-800/70',
          // Legendary gets special glow effect
          rarity === 'Legendary' && 'drop-shadow-lg'
        )}
      />
    </div>
  )
})
