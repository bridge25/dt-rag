/**
 * GlassCard Component
 * Ethereal Glass morphism card with rarity-based glow effects
 *
 * @CODE:GLASS-CARD-IMPL-001
 */

import React, { ReactNode } from "react"
import { cn } from "@/lib/utils"
import { type Rarity, GlassClasses, RarityConfig } from "@/lib/ethereal-glass"

interface GlassCardProps {
  children: ReactNode
  rarity?: Rarity
  className?: string
  onClick?: () => void
}

const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
  ({ children, rarity, className, onClick }, ref) => {
    const rarityClass = rarity ? RarityConfig[rarity].className : ""

    return (
      <div
        ref={ref}
        className={cn(
          "ethereal-card",
          GlassClasses.card,
          GlassClasses.cardHover,
          rarityClass,
          className
        )}
        onClick={onClick}
      >
        {children}
      </div>
    )
  }
)

GlassCard.displayName = "GlassCard"

export { GlassCard }
