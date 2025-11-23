/**
 * Chart Container Component
 * Provides period filtering controls for chart components
 *
 * @CODE:FRONTEND-MIGRATION-002:CHART-CONTAINER
 */
"use client"

import { useState } from "react"

interface ChartContainerProps {
  children: React.ReactNode
  onPeriodChange?: (days: number) => void
}

const PERIOD_OPTIONS = [
  { label: "7 Days", days: 7 },
  { label: "30 Days", days: 30 },
  { label: "All Time", days: 365 },
]

export function ChartContainer({ children, onPeriodChange }: ChartContainerProps) {
  const [selectedPeriod, setSelectedPeriod] = useState(30)

  const handlePeriodChange = (days: number) => {
    setSelectedPeriod(days)
    onPeriodChange?.(days)
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-end gap-2">
        {PERIOD_OPTIONS.map((option) => (
          <button
            key={option.days}
            onClick={() => handlePeriodChange(option.days)}
            className={`
              px-4 py-2 rounded-lg font-medium transition-colors
              ${
                selectedPeriod === option.days
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }
            `}
          >
            {option.label}
          </button>
        ))}
      </div>
      {children}
    </div>
  )
}
