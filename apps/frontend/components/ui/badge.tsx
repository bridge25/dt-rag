/**
 * Badge component with colors and variants
 *
 * @CODE:UI-001
 */

"use client"

import React from "react"

export interface BadgeProps {
  children: React.ReactNode
  color?: "info" | "success" | "warning" | "error" | "purple" | "blue" | "gray" | "dark"
  variant?: "solid" | "outline"
  shape?: "pill" | "square"
  className?: string
}

export function Badge({
  children,
  color = "info",
  variant = "solid",
  shape = "pill",
  className = ""
}: BadgeProps) {
  const baseStyles = "inline-flex items-center px-2.5 py-0.5 text-xs font-medium transition-colors"

  const shapeStyles = {
    pill: "rounded-full",
    square: "rounded"
  }

  const colorStyles = {
    solid: {
      info: "bg-blue-100 text-blue-800",
      success: "bg-green-100 text-green-800",
      warning: "bg-yellow-100 text-yellow-800",
      error: "bg-red-100 text-red-800",
      purple: "bg-purple-100 text-purple-800",
      blue: "bg-blue-100 text-blue-800",
      gray: "bg-gray-100 text-gray-800",
      dark: "bg-gray-800 text-white"
    },
    outline: {
      info: "bg-transparent border border-blue-300 text-blue-700",
      success: "bg-transparent border border-green-300 text-green-700",
      warning: "bg-transparent border border-yellow-300 text-yellow-700",
      error: "bg-transparent border border-red-300 text-red-700",
      purple: "bg-transparent border border-purple-300 text-purple-700",
      blue: "bg-transparent border border-blue-300 text-blue-700",
      gray: "bg-transparent border border-gray-300 text-gray-700",
      dark: "bg-transparent border border-gray-800 text-gray-800"
    }
  }

  return (
    <span
      className={`
        ${baseStyles}
        ${shapeStyles[shape]}
        ${colorStyles[variant][color]}
        ${className}
      `}
    >
      {children}
    </span>
  )
}
