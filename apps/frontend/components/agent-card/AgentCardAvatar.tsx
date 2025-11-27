import { memo } from "react"
import * as LucideIcons from "lucide-react"
import { cn } from "@/lib/utils"
import type { Rarity } from "./types"
import { getDefaultAvatarIcon } from "./types"

interface AgentCardAvatarProps {
  agentId: string
  agentName: string
  rarity: Rarity
  avatarUrl?: string | null
  className?: string
}

const RARITY_GLOWS: Record<Rarity, string> = {
  Common: "shadow-none",
  Rare: "shadow-glow-blue",
  Epic: "shadow-glow-purple",
  Legendary: "shadow-[0_0_30px_rgba(255,215,0,0.3)]",
}

const RARITY_BORDERS: Record<Rarity, string> = {
  Common: "border-white/10",
  Rare: "border-cyan-400/30",
  Epic: "border-purple-400/30",
  Legendary: "border-amber-400/30",
}

export const AgentCardAvatar = memo<AgentCardAvatarProps>(
  function AgentCardAvatar({
    agentId,
    agentName,
    rarity,
    avatarUrl,
    className,
  }) {
    // Use DiceBear as a high-quality fallback if no custom URL is provided
    const displayUrl = avatarUrl || `https://api.dicebear.com/9.x/bottts-neutral/svg?seed=${agentId}&backgroundColor=transparent`

    return (
      <div
        className={cn(
          "relative w-full h-48 rounded-2xl overflow-hidden transition-all duration-500",
          "bg-white/5 backdrop-blur-sm border",
          RARITY_BORDERS[rarity],
          RARITY_GLOWS[rarity],
          "group-hover:scale-[1.02]",
          className
        )}
        role="img"
        aria-label={`${agentName} avatar`}
      >
        {/* Holographic Background Effect */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-50" />

        {/* Animated Shine */}
        <div className="absolute inset-0 -translate-x-full animate-[shimmer_3s_infinite] bg-gradient-to-r from-transparent via-white/10 to-transparent" />

        <div className="relative h-full w-full p-4 flex items-center justify-center">
          <img
            src={displayUrl}
            alt={`${agentName} character`}
            className={cn(
              "w-full h-full object-contain drop-shadow-2xl transition-transform duration-500",
              "group-hover:scale-110 group-hover:drop-shadow-[0_0_15px_rgba(255,255,255,0.3)]"
            )}
            loading="lazy"
            onError={(e) => {
              // Fallback to Lucide icon if image fails
              e.currentTarget.style.display = 'none'
              e.currentTarget.nextElementSibling?.classList.remove('hidden')
            }}
          />

          {/* Fallback Icon (Hidden by default, shown on error) */}
          <div className="hidden absolute inset-0 flex items-center justify-center">
            <LucideIcons.Bot className="w-20 h-20 text-white/20" />
          </div>
        </div>
      </div>
    )
  }
)
