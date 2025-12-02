/**
 * RobotAvatar Component
 * Displays SVG robot avatars with rarity-based glow effects
 *
 * @CODE:ROBOT-AVATAR-IMPL-001
 */

import React, { useState } from "react"
import Image from "next/image"
import { cn } from "@/lib/utils"
import { RarityConfig, type Rarity } from "@/lib/ethereal-glass"

type AvatarSize = "sm" | "md" | "lg"

interface RobotAvatarProps {
  robot: string
  rarity: Rarity
  size?: AvatarSize
  className?: string
}

const sizeConfig: Record<AvatarSize, { container: string; image: string }> = {
  sm: {
    container: "h-16 w-16",
    image: "h-16 w-16",
  },
  md: {
    container: "h-24 w-24",
    image: "h-24 w-24",
  },
  lg: {
    container: "h-32 w-32",
    image: "h-32 w-32",
  },
}

export const RobotAvatar = React.forwardRef<HTMLDivElement, RobotAvatarProps>(
  ({ robot, rarity, size = "md", className }, ref) => {
    const [imageError, setImageError] = useState(false)

    const sizeClasses = sizeConfig[size]
    const _rarityConfig = RarityConfig[rarity] // Prefixed with _ to indicate intentionally unused

    // Build the avatar container classes with rarity-based styling
    const containerClasses = cn(
      "relative flex items-center justify-center",
      "rounded-full overflow-hidden",
      "border-2 border-white/20",
      "backdrop-blur-md",
      "transition-all duration-300 ease-out",
      // Rarity-specific styling
      rarity === "common" && "bg-gray-500/10 shadow-gray-500/20 hover:shadow-gray-500/40",
      rarity === "rare" && "bg-cyan-500/10 shadow-cyan-500/20 hover:shadow-cyan-500/40",
      rarity === "epic" && "bg-purple-500/10 shadow-purple-500/30 hover:shadow-purple-500/50",
      rarity === "legendary" && "bg-amber-500/10 shadow-amber-500/40 hover:shadow-amber-500/60",
      // Size classes
      sizeClasses.container,
      // Animation on hover
      "hover:scale-105 hover:-translate-y-1",
      // Rarity class for additional styling
      `rarity-${rarity}`,
      className
    )

    const avatarPath = `/avatars/robots/${robot}.svg`

    return (
      <div
        ref={ref}
        className={containerClasses}
        role="img"
        aria-label={`${robot} robot avatar - ${rarity} rarity`}
      >
        {!imageError ? (
          <Image
            src={avatarPath}
            alt={`${robot} robot avatar`}
            width={96}
            height={96}
            className={cn(
              sizeClasses.image,
              "object-contain drop-shadow-lg",
              "transition-all duration-300"
            )}
            onError={() => setImageError(true)}
            priority={undefined}
          />
        ) : (
          // Fallback: show initials or placeholder icon
          <div className="flex items-center justify-center w-full h-full bg-white/5">
            <span className="text-lg font-bold text-white/50">
              {robot.charAt(0).toUpperCase()}
            </span>
          </div>
        )}

        {/* Rarity glow effect overlay */}
        {rarity !== "common" && (
          <div
            className={cn(
              "absolute inset-0 rounded-full pointer-events-none",
              "opacity-0 group-hover:opacity-30",
              "transition-opacity duration-300",
              rarity === "rare" && "bg-gradient-to-r from-cyan-400/30 to-blue-400/30",
              rarity === "epic" && "bg-gradient-to-r from-purple-400/40 to-pink-400/40",
              rarity === "legendary" && "bg-gradient-to-r from-amber-300/50 to-yellow-300/50"
            )}
          />
        )}
      </div>
    )
  }
)

RobotAvatar.displayName = "RobotAvatar"
