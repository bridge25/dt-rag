"use client"

import React from "react"

export interface ContainerProps {
  children: React.ReactNode
  glass?: boolean
  className?: string
}

export function Container({ children, glass = false, className = "" }: ContainerProps) {
  const baseStyles = "w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"

  const glassStyles = glass
    ? "backdrop-blur-lg bg-white/10 rounded-lg border border-white/20"
    : ""

  return (
    <div className={`${baseStyles} ${glassStyles} ${className}`}>
      {children}
    </div>
  )
}
