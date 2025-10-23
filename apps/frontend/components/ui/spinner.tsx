"use client"

import React from "react"

export interface SpinnerProps {
  size?: "sm" | "md" | "lg"
  color?: "primary" | "white"
}

export function Spinner({ size = "md", color = "primary" }: SpinnerProps) {
  const sizeClasses = {
    sm: "w-4 h-4 border-2",
    md: "w-6 h-6 border-2",
    lg: "w-8 h-8 border-4"
  }

  const colorClasses = {
    primary: "border-primary-600 border-t-transparent",
    white: "border-white border-t-transparent"
  }

  return (
    <div
      className={`
        ${sizeClasses[size]}
        ${colorClasses[color]}
        rounded-full
        animate-spin
        motion-reduce:animate-none
      `}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  )
}
