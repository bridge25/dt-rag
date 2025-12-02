"use client"

/**
 * Taxonomy Version History Side Panel
 * Displays version history in timeline style with rollback functionality
 *
 * @CODE:FRONTEND-REDESIGN-001-VERSION-PANEL
 *
 * Features:
 * - Timeline-style version history
 * - Active version neon glow highlight
 * - Rollback with confirmation modal
 * - Version selection for viewing
 */

import { useState, useCallback } from "react"
import {
  History,
  Check,
  Calendar,
  FileText,
  RotateCcw,
  ChevronRight,
  AlertTriangle,
  X,
  Sparkles,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useTranslation } from "@/lib/i18n/context"

// Mock version history data
const MOCK_VERSION_HISTORY = [
  {
    version: "1.8.1",
    date: "2025-11-28",
    author: "Admin",
    nodeCount: 18,
    documentCount: 245,
    addedDocs: 47,
    changes: ["Added AI subcategories", "Updated document counts"],
    isActive: true,
  },
  {
    version: "1.8.0",
    date: "2025-11-20",
    author: "Admin",
    nodeCount: 15,
    documentCount: 198,
    addedDocs: 42,
    changes: ["Added Business category", "Restructured Cloud nodes"],
    isActive: false,
  },
  {
    version: "1.7.5",
    date: "2025-11-10",
    author: "System",
    nodeCount: 12,
    documentCount: 156,
    addedDocs: 67,
    changes: ["Initial taxonomy structure", "Added Technology tree"],
    isActive: false,
  },
  {
    version: "1.7.0",
    date: "2025-10-25",
    author: "Admin",
    nodeCount: 8,
    documentCount: 89,
    addedDocs: 89,
    changes: ["Beta release", "Core categories defined"],
    isActive: false,
  },
]

interface TaxonomyVersionPanelProps {
  currentVersion: string
  onVersionChange?: (version: string) => void
  onRollback?: (version: string) => Promise<void>
  className?: string
}

// Rollback Confirmation Modal Component
function RollbackModal({
  isOpen,
  version,
  onConfirm,
  onCancel,
  isLoading,
}: {
  isOpen: boolean
  version: string
  onConfirm: () => void
  onCancel: () => void
  isLoading: boolean
}) {
  const { t } = useTranslation()

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Modal */}
      <div
        className={cn(
          "relative z-10 w-full max-w-md mx-4",
          "bg-slate-900/95 backdrop-blur-xl",
          "border border-white/10 rounded-2xl",
          "shadow-[0_8px_32px_rgba(0,0,0,0.5),_0_0_30px_rgba(251,191,36,0.2)]",
          "animate-in fade-in zoom-in-95 duration-200"
        )}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-6 py-4 border-b border-white/10">
          <div className="p-2 rounded-lg bg-amber-500/20">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">
              {t("taxonomy.rollbackConfirm")}
            </h3>
          </div>
          <button
            onClick={onCancel}
            className="ml-auto p-1.5 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5 text-white/60" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5">
          <p className="text-white/70 text-sm leading-relaxed">
            {t("taxonomy.rollbackWarning", { version })}
          </p>

          <div className="mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
            <div className="flex items-center gap-2 text-amber-400 text-sm font-medium">
              <RotateCcw className="w-4 h-4" />
              <span>Target: v{version}</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center gap-3 px-6 py-4 border-t border-white/10 bg-white/[0.02]">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className={cn(
              "flex-1 px-4 py-2.5 rounded-lg",
              "text-white/70 text-sm font-medium",
              "border border-white/10",
              "hover:bg-white/5 hover:border-white/20",
              "transition-all duration-200",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {t("taxonomy.rollbackCancel")}
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={cn(
              "flex-1 px-4 py-2.5 rounded-lg",
              "bg-gradient-to-r from-amber-500 to-orange-500",
              "text-white text-sm font-semibold",
              "shadow-lg shadow-amber-500/30",
              "hover:shadow-[0_0_20px_rgba(251,191,36,0.5)]",
              "transition-all duration-300",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              isLoading && "animate-pulse"
            )}
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <RotateCcw className="w-4 h-4 animate-spin" />
                Processing...
              </span>
            ) : (
              t("taxonomy.rollbackExecute")
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export function TaxonomyVersionPanel({
  currentVersion,
  onVersionChange,
  onRollback,
  className,
}: TaxonomyVersionPanelProps) {
  const { t } = useTranslation()
  const [selectedVersion, setSelectedVersion] = useState(currentVersion)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [rollbackTarget, setRollbackTarget] = useState<string | null>(null)
  const [isRollbackLoading, setIsRollbackLoading] = useState(false)

  const handleVersionSelect = useCallback(
    (version: string) => {
      setSelectedVersion(version)
      onVersionChange?.(version)
    },
    [onVersionChange]
  )

  const handleRollback = useCallback(async () => {
    if (!rollbackTarget) return

    setIsRollbackLoading(true)
    try {
      if (onRollback) {
        await onRollback(rollbackTarget)
      } else {
        // Mock rollback delay
        await new Promise((resolve) => setTimeout(resolve, 1500))
      }
      // After successful rollback, update the selected version
      setSelectedVersion(rollbackTarget)
      onVersionChange?.(rollbackTarget)
    } catch (error) {
      console.error("Rollback failed:", error)
    } finally {
      setIsRollbackLoading(false)
      setRollbackTarget(null)
    }
  }, [rollbackTarget, onRollback, onVersionChange])

  return (
    <>
      {/* Side Panel */}
      <div
        className={cn(
          "flex flex-col",
          "bg-slate-900/80 backdrop-blur-xl",
          "border-l border-white/10",
          "transition-all duration-300 ease-out",
          isCollapsed ? "w-12" : "w-72",
          className
        )}
      >
        {/* Header */}
        <div
          className={cn(
            "flex items-center gap-3 px-4 py-4",
            "border-b border-white/10",
            "bg-white/[0.02]"
          )}
        >
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className={cn(
              "p-2 rounded-lg",
              "bg-cyan-500/10 border border-cyan-400/20",
              "hover:bg-cyan-500/20 hover:border-cyan-400/40",
              "transition-all duration-200"
            )}
          >
            <History
              className={cn(
                "w-5 h-5 text-cyan-400",
                "drop-shadow-[0_0_8px_rgba(0,247,255,0.7)]"
              )}
            />
          </button>

          {!isCollapsed && (
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-semibold text-white flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                {t("taxonomy.versionHistory")}
              </h3>
              <p className="text-xs text-white/40 mt-0.5 truncate">
                {t("taxonomy.selectVersion")}
              </p>
            </div>
          )}
        </div>

        {/* Version List */}
        {!isCollapsed && (
          <div className="flex-1 overflow-y-auto custom-scrollbar py-2">
            {MOCK_VERSION_HISTORY.map((version, index) => {
              const isSelected = version.version === selectedVersion
              const isActive = version.isActive
              const isLast = index === MOCK_VERSION_HISTORY.length - 1

              return (
                <div key={version.version} className="relative px-4">
                  {/* Timeline connector */}
                  {!isLast && (
                    <div
                      className={cn(
                        "absolute left-7 top-10 w-0.5 h-[calc(100%-16px)]",
                        isActive
                          ? "bg-gradient-to-b from-cyan-400/50 to-cyan-400/10"
                          : "bg-white/10"
                      )}
                    />
                  )}

                  <button
                    onClick={() => handleVersionSelect(version.version)}
                    className={cn(
                      "relative w-full py-3 text-left",
                      "transition-all duration-200",
                      "group"
                    )}
                  >
                    <div className="flex items-start gap-3">
                      {/* Timeline dot */}
                      <div
                        className={cn(
                          "relative z-10 flex items-center justify-center",
                          "w-6 h-6 rounded-full",
                          "border-2 transition-all duration-300",
                          isActive
                            ? cn(
                                "bg-cyan-500/30 border-cyan-400",
                                "shadow-[0_0_15px_rgba(0,247,255,0.5)]"
                              )
                            : isSelected
                            ? "bg-white/20 border-white/50"
                            : "bg-slate-800 border-white/20 group-hover:border-white/40"
                        )}
                      >
                        {isActive && (
                          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                        )}
                        {!isActive && isSelected && (
                          <Check className="w-3 h-3 text-white/80" />
                        )}
                      </div>

                      {/* Content */}
                      <div
                        className={cn(
                          "flex-1 min-w-0 p-3 rounded-xl",
                          "border transition-all duration-300",
                          isActive
                            ? cn(
                                "bg-cyan-500/10 border-cyan-400/30",
                                "shadow-[0_0_20px_rgba(0,247,255,0.15)]"
                              )
                            : isSelected
                            ? "bg-white/10 border-white/20"
                            : "bg-white/5 border-white/5 group-hover:border-white/10 group-hover:bg-white/[0.07]"
                        )}
                      >
                        {/* Version Header */}
                        <div className="flex items-center justify-between gap-2">
                          <span
                            className={cn(
                              "text-sm font-semibold",
                              isActive
                                ? "text-cyan-300 drop-shadow-[0_0_5px_rgba(0,247,255,0.5)]"
                                : isSelected
                                ? "text-white"
                                : "text-white/80"
                            )}
                          >
                            v{version.version}
                          </span>
                          {isActive && (
                            <span className="px-1.5 py-0.5 text-[10px] font-bold bg-cyan-500/30 text-cyan-300 rounded uppercase tracking-wider">
                              {t("taxonomy.active")}
                            </span>
                          )}
                        </div>

                        {/* Metadata */}
                        <div className="flex items-center gap-2 mt-1.5 text-xs text-white/40">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {version.date}
                          </span>
                        </div>

                        {/* Stats */}
                        <div className="flex items-center gap-2 mt-2 text-xs">
                          <span className="text-white/50">
                            {version.nodeCount} nodes
                          </span>
                          <span className="text-white/30">•</span>
                          <span className="text-white/50">
                            {version.documentCount} docs
                          </span>
                          {version.addedDocs > 0 && (
                            <>
                              <span className="text-white/30">•</span>
                              <span className="text-green-400/80">
                                +{version.addedDocs}
                              </span>
                            </>
                          )}
                        </div>

                        {/* Changes */}
                        {version.changes.length > 0 && (
                          <div className="mt-2 space-y-1">
                            {version.changes.slice(0, 2).map((change, idx) => (
                              <div
                                key={idx}
                                className="flex items-start gap-1.5 text-xs text-white/30"
                              >
                                <ChevronRight className="w-3 h-3 mt-0.5 flex-shrink-0 text-white/20" />
                                <span className="line-clamp-1">{change}</span>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Rollback Button - Only for non-active versions */}
                        {!isActive && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              setRollbackTarget(version.version)
                            }}
                            className={cn(
                              "mt-3 w-full flex items-center justify-center gap-1.5",
                              "px-3 py-1.5 rounded-lg",
                              "text-xs font-medium",
                              "bg-amber-500/10 border border-amber-500/20",
                              "text-amber-400/80",
                              "opacity-0 group-hover:opacity-100",
                              "hover:bg-amber-500/20 hover:border-amber-500/30",
                              "hover:shadow-[0_0_10px_rgba(251,191,36,0.3)]",
                              "transition-all duration-200"
                            )}
                          >
                            <RotateCcw className="w-3 h-3" />
                            {t("taxonomy.rollback")}
                          </button>
                        )}
                      </div>
                    </div>
                  </button>
                </div>
              )
            })}
          </div>
        )}

        {/* Footer */}
        {!isCollapsed && (
          <div className="px-4 py-3 border-t border-white/10 bg-white/[0.02]">
            <div className="flex items-center justify-between text-xs">
              <span className="text-white/40">{t("taxonomy.selectedVersion")}</span>
              <span className="text-cyan-400 font-medium flex items-center gap-1">
                <FileText className="w-3 h-3" />v{selectedVersion}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Rollback Confirmation Modal */}
      <RollbackModal
        isOpen={rollbackTarget !== null}
        version={rollbackTarget || ""}
        onConfirm={handleRollback}
        onCancel={() => setRollbackTarget(null)}
        isLoading={isRollbackLoading}
      />
    </>
  )
}
