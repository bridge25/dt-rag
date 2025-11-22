"use client"

/**
 * Loading spinner component with animated border
 * @CODE:FRONTEND-MIGRATION-001
 */

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="relative w-16 h-16">
        <div className="absolute top-0 left-0 w-full h-full border-4 border-blue-200 rounded-full" />
        <div className="absolute top-0 left-0 w-full h-full border-4 border-blue-600 rounded-full animate-spin border-t-transparent" />
      </div>
    </div>
  )
}
