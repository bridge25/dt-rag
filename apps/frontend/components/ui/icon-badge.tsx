/**
 * Icon badge component
 *
 * @CODE:UI-001
 */

import { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface IconBadgeProps {
  icon: LucideIcon
  color?: "orange" | "red" | "blue" | "green" | "purple" | "teal"
  size?: "sm" | "md" | "lg"
  className?: string
}

const colorClasses = {
  orange: "bg-orangePrimary/20 text-orangePrimary",
  red: "bg-red-500/20 text-red-500",
  blue: "bg-blue-500/20 text-blue-500",
  green: "bg-greenFolder/20 text-greenFolder",
  purple: "bg-purpleFolder/20 text-purpleFolder",
  teal: "bg-tealAccent/20 text-tealAccent",
}

const sizeClasses = {
  sm: "w-8 h-8",
  md: "w-12 h-12",
  lg: "w-16 h-16",
}

const iconSizeClasses = {
  sm: "w-4 h-4",
  md: "w-6 h-6",
  lg: "w-8 h-8",
}

export function IconBadge({ icon: Icon, color = "orange", size = "md", className }: IconBadgeProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full transition-transform hover:scale-110",
        colorClasses[color],
        sizeClasses[size],
        className
      )}
    >
      <Icon className={iconSizeClasses[size]} />
    </div>
  )
}
