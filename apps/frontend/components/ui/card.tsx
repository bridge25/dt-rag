/**
 * Card component with elevation and hover effects
 *
 * @CODE:UI-001
 */

"use client"

import React from "react"

export interface CardProps {
  children: React.ReactNode
  elevation?: 0 | 1 | 2 | 3 | 4
  hoverable?: boolean
  className?: string
  onClick?: () => void
}

export function Card({
  children,
  elevation = 1,
  hoverable = false,
  className = "",
  onClick
}: CardProps) {
  const baseStyles = "bg-white rounded-lg transition-all duration-normal"

  const elevationStyles = {
    0: "shadow-none",
    1: "shadow-elevation-1",
    2: "shadow-elevation-2",
    3: "shadow-elevation-3",
    4: "shadow-elevation-4"
  }

  const hoverStyles = hoverable
    ? "hover:shadow-elevation-2 hover:-translate-y-0.5 motion-reduce:hover:translate-y-0 cursor-pointer"
    : ""

  return (
    <div
      className={`
        ${baseStyles}
        ${elevationStyles[elevation]}
        ${hoverStyles}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyPress={onClick ? (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          onClick()
        }
      } : undefined}
    >
      {children}
    </div>
  )
}

export function CardHeader({
  children,
  className = ""
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`p-6 border-b border-gray-200 ${className}`}>
      {children}
    </div>
  )
}

export function CardContent({
  children,
  className = ""
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`p-6 ${className}`}>
      {children}
    </div>
  )
}

export function CardFooter({
  children,
  className = ""
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`p-6 border-t border-gray-200 ${className}`}>
      {children}
    </div>
  )
}
