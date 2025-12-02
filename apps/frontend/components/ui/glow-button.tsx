/**
 * GlowButton Component
 * Neon glow button with ethereal effects
 *
 * @CODE:GLOW-BUTTON-IMPL-001
 */

import React, { ButtonHTMLAttributes, ReactNode } from "react"
import { cn } from "@/lib/utils"
import { GlassClasses } from "@/lib/ethereal-glass"

type GlowVariant = "cyan" | "purple" | "gold" | "green"
type ButtonSize = "sm" | "md" | "lg"

interface GlowButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: GlowVariant
  size?: ButtonSize
}

const sizeClasses: Record<ButtonSize, string> = {
  sm: "px-3 py-1 text-sm",
  md: "px-4 py-2 text-base",
  lg: "px-6 py-3 text-lg",
}

const variantClasses: Record<GlowVariant, string> = {
  cyan: "glow-cyan",
  purple: "glow-purple",
  gold: "glow-gold",
  green: "glow-green",
}

const GlowButton = React.forwardRef<HTMLButtonElement, GlowButtonProps>(
  (
    {
      children,
      variant = "cyan",
      size = "md",
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(
          GlassClasses.button,
          GlassClasses.buttonHover,
          "disabled:opacity-50",
          "disabled:cursor-not-allowed",
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      >
        <span className="relative z-10">
          {children}
        </span>
      </button>
    )
  }
)

GlowButton.displayName = "GlowButton"

export { GlowButton }
