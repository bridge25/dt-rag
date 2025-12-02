"use client"

/**
 * AgentCreationModal - Create Agent from Taxonomy Selection
 *
 * Pokemon card style agent creation flow:
 * - Pre-filled taxonomy scope from selected node
 * - Agent name input
 * - Avatar/Robot selection
 * - Rarity selection (based on taxonomy depth)
 *
 * @CODE:FRONTEND-REDESIGN-001-AGENT-CREATION
 */

import { useState, useMemo } from "react"
import Image from "next/image"
import { X, Bot, Sparkles, Check } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTranslation } from "@/lib/i18n/context"
import type { Rarity } from "@/lib/api/types"

interface AgentCreationModalProps {
  isOpen: boolean
  onClose: () => void
  taxonomyPath: string[] // Selected taxonomy path, e.g., ["Technology", "AI", "Machine Learning"]
  onCreateAgent?: (agent: {
    name: string
    taxonomy_scope: string[]
    rarity: Rarity
    avatar: string
  }) => void
}

// Available robot avatars by rarity
const ROBOT_AVATARS: Record<Rarity, string[]> = {
  Common: [
    "/assets/agents/nobg/common/robot-common-01.png",
    "/assets/agents/nobg/common/robot-common-02.png",
    "/assets/agents/nobg/common/robot-common-03.png",
    "/assets/agents/nobg/common/robot-common-04.png",
  ],
  Rare: [
    "/assets/agents/nobg/rare/robot-rare-01.png",
    "/assets/agents/nobg/rare/robot-rare-02.png",
    "/assets/agents/nobg/rare/robot-rare-03.png",
    "/assets/agents/nobg/rare/robot-rare-04.png",
  ],
  Epic: [
    "/assets/agents/nobg/epic/robot-epic-01.png",
    "/assets/agents/nobg/epic/robot-epic-02.png",
    "/assets/agents/nobg/epic/robot-epic-03.png",
    "/assets/agents/nobg/epic/robot-epic-04.png",
  ],
  Legendary: [
    "/assets/agents/nobg/legendary/robot-legendary-01.png",
    "/assets/agents/nobg/legendary/robot-legendary-02.png",
    "/assets/agents/nobg/legendary/robot-legendary-03.png",
  ],
}

// Rarity styling configuration
const RARITY_STYLES: Record<Rarity, { border: string; bg: string; text: string; glow: string }> = {
  Common: {
    border: "border-slate-400/50",
    bg: "bg-slate-500/20",
    text: "text-slate-300",
    glow: "shadow-[0_0_15px_rgba(148,163,184,0.3)]",
  },
  Rare: {
    border: "border-cyan-400/50",
    bg: "bg-cyan-500/20",
    text: "text-cyan-300",
    glow: "shadow-[0_0_15px_rgba(0,247,255,0.4)]",
  },
  Epic: {
    border: "border-purple-400/50",
    bg: "bg-purple-500/20",
    text: "text-purple-300",
    glow: "shadow-[0_0_15px_rgba(139,92,246,0.4)]",
  },
  Legendary: {
    border: "border-amber-400/50",
    bg: "bg-amber-500/20",
    text: "text-amber-300",
    glow: "shadow-[0_0_20px_rgba(251,191,36,0.5)]",
  },
}

export function AgentCreationModal({
  isOpen,
  onClose,
  taxonomyPath,
  onCreateAgent,
}: AgentCreationModalProps) {
  const { t } = useTranslation()
  const [agentName, setAgentName] = useState("")
  const [selectedRarity, setSelectedRarity] = useState<Rarity>("Common")
  const [selectedAvatar, setSelectedAvatar] = useState<string>(ROBOT_AVATARS.Common[0])
  const [isCreating, setIsCreating] = useState(false)

  // Suggest rarity based on taxonomy depth
  const suggestedRarity = useMemo((): Rarity => {
    const depth = taxonomyPath.length
    if (depth >= 4) return "Legendary"
    if (depth >= 3) return "Epic"
    if (depth >= 2) return "Rare"
    return "Common"
  }, [taxonomyPath])

  // Format taxonomy path for display
  const displayPath = useMemo(() => {
    return "/" + taxonomyPath.join("/")
  }, [taxonomyPath])

  // Handle rarity change and update avatar
  const handleRarityChange = (rarity: Rarity) => {
    setSelectedRarity(rarity)
    setSelectedAvatar(ROBOT_AVATARS[rarity][0])
  }

  // Handle agent creation
  const handleCreate = async () => {
    if (!agentName.trim()) return

    setIsCreating(true)
    try {
      await onCreateAgent?.({
        name: agentName.trim(),
        taxonomy_scope: taxonomyPath,
        rarity: selectedRarity,
        avatar: selectedAvatar,
      })
      onClose()
    } catch (error) {
      console.error("Failed to create agent:", error)
    } finally {
      setIsCreating(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={cn(
          "relative w-full max-w-lg mx-4",
          "bg-slate-900/95 backdrop-blur-xl",
          "border border-white/10 rounded-2xl",
          "shadow-2xl shadow-black/50",
          "animate-in fade-in zoom-in-95 duration-200"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-500/20 border border-cyan-400/30">
              <Bot className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                {t("agents.creation.title")}
              </h2>
              <p className="text-xs text-white/50">
                {t("agents.creation.subtitle")}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5 text-white/60" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-5 space-y-5">
          {/* Taxonomy Scope (Read-only) */}
          <div>
            <label className="block text-xs font-medium text-white/60 uppercase tracking-wider mb-2">
              {t("agents.card.expertise")}
            </label>
            <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-white/5 border border-white/10">
              <span className="text-white/40">📚</span>
              <span className="text-cyan-300 font-medium">{displayPath}</span>
            </div>
          </div>

          {/* Agent Name */}
          <div>
            <label className="block text-xs font-medium text-white/60 uppercase tracking-wider mb-2">
              {t("agents.creation.name")}
            </label>
            <input
              type="text"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              placeholder={t("agents.creation.namePlaceholder")}
              className={cn(
                "w-full px-4 py-3 rounded-lg",
                "bg-white/5 border border-white/20",
                "text-white placeholder:text-white/40",
                "focus:outline-none focus:border-cyan-400/50 focus:ring-2 focus:ring-cyan-400/20",
                "transition-all"
              )}
            />
          </div>

          {/* Rarity Selection */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-white/60 uppercase tracking-wider">
                {t("agents.creation.rarity")}
              </label>
              <span className="text-xs text-white/40">
                {t("agents.creation.suggested")}: {suggestedRarity}
              </span>
            </div>
            <div className="grid grid-cols-4 gap-2">
              {(["Common", "Rare", "Epic", "Legendary"] as Rarity[]).map((rarity) => (
                <button
                  key={rarity}
                  onClick={() => handleRarityChange(rarity)}
                  className={cn(
                    "px-3 py-2 rounded-lg text-xs font-semibold",
                    "border transition-all duration-200",
                    selectedRarity === rarity
                      ? cn(RARITY_STYLES[rarity].border, RARITY_STYLES[rarity].bg, RARITY_STYLES[rarity].text, RARITY_STYLES[rarity].glow)
                      : "border-white/10 text-white/60 hover:bg-white/5"
                  )}
                >
                  {t(`agents.rarity.${rarity.toLowerCase()}`)}
                </button>
              ))}
            </div>
          </div>

          {/* Avatar Selection */}
          <div>
            <label className="block text-xs font-medium text-white/60 uppercase tracking-wider mb-2">
              {t("agents.creation.avatar")}
            </label>
            <div className="grid grid-cols-4 gap-3">
              {ROBOT_AVATARS[selectedRarity].map((avatar, index) => (
                <button
                  key={avatar}
                  onClick={() => setSelectedAvatar(avatar)}
                  className={cn(
                    "relative aspect-square rounded-xl overflow-hidden",
                    "border-2 transition-all duration-200",
                    selectedAvatar === avatar
                      ? cn(RARITY_STYLES[selectedRarity].border, RARITY_STYLES[selectedRarity].glow, "scale-105")
                      : "border-white/10 hover:border-white/30"
                  )}
                >
                  <div className="absolute inset-0 bg-gradient-to-b from-slate-800/50 to-slate-900/80" />
                  <Image
                    src={avatar}
                    alt={`Robot ${index + 1}`}
                    width={80}
                    height={80}
                    className="w-full h-full object-contain p-2 relative z-10"
                    unoptimized
                  />
                  {selectedAvatar === avatar && (
                    <div className="absolute top-1 right-1 p-1 rounded-full bg-cyan-500 z-20">
                      <Check className="w-3 h-3 text-white" />
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/10">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm font-medium text-white/60 hover:bg-white/10 transition-colors"
          >
            {t("common.cancel")}
          </button>
          <button
            onClick={handleCreate}
            disabled={!agentName.trim() || isCreating}
            className={cn(
              "flex items-center gap-2 px-5 py-2 rounded-lg",
              "text-sm font-semibold text-white",
              "bg-gradient-to-r from-cyan-500 to-purple-500",
              "shadow-lg shadow-cyan-500/25",
              "transition-all duration-200",
              "hover:shadow-[0_0_20px_rgba(0,247,255,0.5)]",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {isCreating ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                {t("agents.creation.creating")}
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                {t("agents.creation.create")}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
