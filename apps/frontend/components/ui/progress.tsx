/**
 * Progress bar component
 *
 * @CODE:UI-001
 */

"use client"

import React from "react"

export interface ProgressProps {
  value: number
  showLabel?: boolean
  color?: "primary" | "accent"
  className?: string
}

export function Progress({ value, showLabel = false, color = "primary", className = "" }: ProgressProps) {
  const clampedValue = Math.min(100, Math.max(0, value))

  const colorClasses = {
    primary: "bg-gradient-to-r from-purple-600 to-slate-800",
    accent: "bg-gradient-to-r from-purple-500 to-blue-500"
  }

  return (
    <div className="w-full">
      <div
        className={`relative h-2 bg-gray-200 rounded-full overflow-hidden ${className}`}
        role="progressbar"
        aria-valuenow={clampedValue}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={`h-full transition-all duration-normal ease-out motion-reduce:duration-0 ${colorClasses[color]}`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
      {showLabel && (
        <p className="mt-2 text-sm text-center font-medium text-gray-700">
          {clampedValue}%
        </p>
      )}
    </div>
  )
}
