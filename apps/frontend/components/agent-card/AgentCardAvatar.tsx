import { memo, useState } from "react"
import Image from "next/image"
import * as LucideIcons from "lucide-react"
import { cn } from "@/lib/utils"
import type { Rarity } from "./types"

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
    const [hasError, setHasError] = useState(false)

    // Default fallback to local robot images based on rarity
    const getFallbackImage = () => {
      const rarityPath = rarity.toLowerCase()
      const index = (parseInt(agentId.replace(/\D/g, ""), 10) % 4) + 1
      return `/assets/agents/nobg/${rarityPath}/robot-${rarityPath}-0${index}.png`
    }

    const displayUrl = avatarUrl || getFallbackImage()

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
          {!hasError ? (
            <Image
              src={displayUrl}
              alt={`${agentName} character`}
              fill
              sizes="(max-width: 768px) 50vw, 192px"
              className={cn(
                "object-contain drop-shadow-2xl transition-transform duration-500",
                "group-hover:scale-110 group-hover:drop-shadow-[0_0_15px_rgba(255,255,255,0.3)]"
              )}
              onError={() => setHasError(true)}
            />
          ) : (
            /* Fallback Icon when image fails to load */
            <LucideIcons.Bot className="w-20 h-20 text-white/20" />
          )}
        </div>
      </div>
    )
  }
)
