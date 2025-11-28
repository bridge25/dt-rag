/**
 * Constellation Control Panel Component
 *
 * Glass morphism control panel for taxonomy constellation visualization with:
 * - Zoom In/Out controls
 * - Filter dropdown
 * - Settings dropdown
 * - Data Density slider
 *
 * Design Reference: 뉴디자인2.png (bottom-left control panel)
 * @CODE:FRONTEND-REDESIGN-001-CONTROL-PANEL
 */

"use client"

import { ZoomIn, ZoomOut, Filter, Settings, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface ConstellationControlPanelProps {
  onZoomIn: () => void
  onZoomOut: () => void
  onFilterClick: () => void
  onSettingsClick: () => void
  dataDensity: number
  onDataDensityChange: (value: number) => void
  className?: string
}

interface ControlButtonProps {
  icon: React.ReactNode
  label: string
  hasArrow?: boolean
  onClick: () => void
  disabled?: boolean
}

/**
 * Individual control button component
 */
function ControlButton({
  icon,
  label,
  hasArrow = false,
  onClick,
  disabled = false
}: ControlButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "flex items-center gap-3 w-full px-3 py-2 rounded-lg",
        "text-xs font-medium text-gray-200 uppercase tracking-wider",
        "transition-colors duration-200",
        "hover:bg-white/10 active:bg-white/20",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/50"
      )}
    >
      <span className="w-5 h-5 flex items-center justify-center opacity-80">
        {icon}
      </span>
      <span className="flex-1 text-left">{label}</span>
      {hasArrow && (
        <span className="w-4 h-4 flex items-center justify-center opacity-60 ml-auto">
          <ChevronRight size={14} />
        </span>
      )}
    </button>
  )
}

/**
 * Main ConstellationControlPanel component
 */
export default function ConstellationControlPanel({
  onZoomIn,
  onZoomOut,
  onFilterClick,
  onSettingsClick,
  dataDensity,
  onDataDensityChange,
  className
}: ConstellationControlPanelProps) {
  const handleDensityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onDataDensityChange(Number(e.target.value))
  }

  return (
    <div
      className={cn(
        "absolute bottom-6 left-6 z-10",
        "w-64",
        "bg-slate-800/60 backdrop-blur-xl",
        "border border-white/10 rounded-xl",
        "p-4 space-y-3",
        "shadow-2xl shadow-black/50",
        className
      )}
      data-testid="constellation-control-panel"
    >
      {/* Zoom Controls */}
      <ControlButton
        icon={<ZoomIn size={18} />}
        label="Zoom In"
        onClick={onZoomIn}
      />
      <ControlButton
        icon={<ZoomOut size={18} />}
        label="Zoom Out"
        onClick={onZoomOut}
      />

      {/* Filter Control with Arrow */}
      <ControlButton
        icon={<Filter size={18} />}
        label="Filter"
        hasArrow={true}
        onClick={onFilterClick}
      />

      {/* Settings Control with Arrow */}
      <ControlButton
        icon={<Settings size={18} />}
        label="Settings"
        hasArrow={true}
        onClick={onSettingsClick}
      />

      {/* Divider */}
      <div className="border-t border-white/10" />

      {/* Data Density Section */}
      <div className="space-y-3 pt-1">
        <label className="block text-xs font-medium text-gray-300 uppercase tracking-wider">
          Data Density
        </label>
        <input
          type="range"
          min="0"
          max="100"
          value={dataDensity}
          onChange={handleDensityChange}
          data-testid="data-density-slider"
          className={cn(
            "w-full h-1.5 rounded-full accent-cyan-400",
            "appearance-none bg-gradient-to-r from-white/20 to-white/5",
            "hover:bg-gradient-to-r hover:from-white/30 hover:to-white/10",
            "focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/50",
            "[&::-webkit-slider-thumb]:appearance-none",
            "[&::-webkit-slider-thumb]:w-4",
            "[&::-webkit-slider-thumb]:h-4",
            "[&::-webkit-slider-thumb]:rounded-full",
            "[&::-webkit-slider-thumb]:bg-cyan-400",
            "[&::-webkit-slider-thumb]:cursor-pointer",
            "[&::-webkit-slider-thumb]:shadow-lg",
            "[&::-webkit-slider-thumb]:shadow-cyan-500/50",
            "[&::-webkit-slider-thumb]:hover:bg-cyan-300",
            "[&::-webkit-slider-thumb]:transition-colors",
            "[&::-moz-range-thumb]:w-4",
            "[&::-moz-range-thumb]:h-4",
            "[&::-moz-range-thumb]:rounded-full",
            "[&::-moz-range-thumb]:bg-cyan-400",
            "[&::-moz-range-thumb]:cursor-pointer",
            "[&::-moz-range-thumb]:border-0",
            "[&::-moz-range-thumb]:shadow-lg",
            "[&::-moz-range-thumb]:shadow-cyan-500/50",
            "[&::-moz-range-thumb]:hover:bg-cyan-300",
            "[&::-moz-range-thumb]:transition-colors"
          )}
          aria-label="Data density control (0-100)"
        />
        <div className="text-xs text-gray-400">
          Density: {dataDensity}%
        </div>
      </div>
    </div>
  )
}
