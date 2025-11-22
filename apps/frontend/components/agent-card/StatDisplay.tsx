"use client"

/**
 * StatDisplay Component
 * @CODE:FRONTEND-MIGRATION-001
 */

import { memo, type ReactNode } from "react"
import { cn } from "@/lib/utils"

interface StatDisplayProps {
  label: string
  value: string | number
  icon?: ReactNode
  variant?: "default" | "primary" | "success" | "warning"
  layout?: "vertical" | "horizontal"
  className?: string
}

const variantStyles = {
  default: "text-gray-900",
  primary: "text-primary",
  success: "text-green-600",
  warning: "text-yellow-600",
}

export const StatDisplay = memo<StatDisplayProps>(function StatDisplay({
  label,
  value,
  icon,
  variant = "default",
  layout = "vertical",
  className,
}) {
  return (
    <div
      className={cn(
        "flex gap-2",
        layout === "vertical" ? "flex-col items-start" : "flex-row items-center",
        className
      )}
    >
      <div className="flex items-center gap-1.5">
        {icon && <span className="text-gray-500">{icon}</span>}
        <span className="text-sm text-gray-600">{label}</span>
      </div>
      <span className={cn("text-lg font-semibold", variantStyles[variant])}>
        {value}
      </span>
    </div>
  )
})
