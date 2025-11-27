/**
 * Card component with Ethereal Glass aesthetic
 *
 * @CODE:UI-002
 */

"use client"

import React from "react"
import { cn } from "@/lib/utils"

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  elevation?: 0 | 1 | 2 | 3 | 4
  hoverable?: boolean
  glass?: boolean
}

export function Card({
  children,
  elevation = 1,
  hoverable = false,
  glass = true,
  className,
  onClick,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl transition-all duration-300",
        // Glass styles (default)
        glass && "bg-white/5 border border-white/10 backdrop-blur-md shadow-glass",
        // Hover effects
        hoverable && "hover:bg-white/10 hover:border-white/20 hover:shadow-glass-hover hover:-translate-y-0.5 cursor-pointer",
        // Non-glass fallback (if needed)
        !glass && "bg-card text-card-foreground border shadow-sm",
        className
      )}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          onClick(e as any)
        }
      } : undefined}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({
  children,
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("flex flex-col space-y-1.5 p-6 border-b border-white/5", className)} {...props}>
      {children}
    </div>
  )
}

export function CardTitle({
  children,
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn("text-2xl font-semibold leading-none tracking-tight text-white", className)} {...props}>
      {children}
    </h3>
  )
}

export function CardDescription({
  children,
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-sm text-white/60", className)} {...props}>
      {children}
    </p>
  )
}

export function CardContent({
  children,
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("p-6", className)} {...props}>
      {children}
    </div>
  )
}

export function CardFooter({
  children,
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("flex items-center p-6 pt-0 border-t border-white/5 mt-auto", className)} {...props}>
      {children}
    </div>
  )
}
