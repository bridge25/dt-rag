"use client"

/**
 * RarityBadge Component
 * @CODE:FRONTEND-MIGRATION-001
 */

import { memo } from "react"
import { cn } from "@/lib/utils"
import type { Rarity } from "./types"

interface RarityBadgeProps {
  rarity: Rarity
  className?: string
}

export const RarityBadge = memo<RarityBadgeProps>(function RarityBadge({
  rarity,
  className,
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide",
        rarity === "Common" && "bg-gray-500 text-white",
        rarity === "Rare" && "bg-blue-500 text-white",
        rarity === "Epic" && "bg-purple-600 text-white",
        rarity === "Legendary" && "bg-amber-500 text-black",
        className
      )}
      aria-label={`Rarity: ${rarity}`}
    >
      {rarity}
    </span>
  )
})
