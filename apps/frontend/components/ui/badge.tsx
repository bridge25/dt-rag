/**
 * Badge component with Ethereal Glass aesthetic
 *
 * @CODE:UI-002
 */

"use client"

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 backdrop-blur-sm",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-blue-500/20 text-blue-100 hover:bg-blue-500/30 border-blue-500/30 shadow-[0_0_10px_rgba(59,130,246,0.2)]",
        secondary:
          "border-transparent bg-white/10 text-white hover:bg-white/20 border-white/10",
        destructive:
          "border-transparent bg-red-500/20 text-red-100 hover:bg-red-500/30 border-red-500/30",
        outline: "text-white border-white/20",
        glass: "bg-white/5 border-white/10 text-white shadow-glass",
        glow: "bg-blue-500/10 border-blue-500/50 text-blue-300 shadow-[0_0_10px_rgba(59,130,246,0.3)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
  VariantProps<typeof badgeVariants> { }

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
