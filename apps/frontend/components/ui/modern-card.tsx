import { ReactNode, HTMLAttributes } from "react"
import { cn } from "@/lib/utils"

interface ModernCardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "dark" | "teal" | "beige" | "purple" | "green" | "default"
  className?: string
  children: ReactNode
}

const variantClasses = {
  dark: "bg-darkCard text-white",
  teal: "bg-tealAccent text-gray-900",
  beige: "bg-beigeAccent text-gray-900",
  purple: "bg-purpleFolder text-white",
  green: "bg-greenFolder text-white",
  default: "bg-card text-card-foreground",
}

export function ModernCard({ variant = "default", className, children, ...props }: ModernCardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl shadow-soft p-6 transition-all hover:shadow-soft-lg",
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
