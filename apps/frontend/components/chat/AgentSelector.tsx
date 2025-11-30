"use client"

/**
 * Agent Selector Component for Chat Page
 * Allows users to select which agent to use for search/chat
 *
 * @CODE:FRONTEND-REDESIGN-001-AGENT-SELECTOR
 */

import { useState, useRef, useEffect } from "react"
import Image from "next/image"
import { Bot, ChevronDown, Check, Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAgents } from "@/hooks/useAgents"
import { useTranslation } from "@/lib/i18n/context"
import type { AgentCardData, Rarity } from "@/components/agent-card/types"

interface AgentSelectorProps {
  selectedAgentId: string | null
  onSelectAgent: (agent: AgentCardData | null) => void
  className?: string
}

const RARITY_COLORS: Record<Rarity, { text: string; bg: string; border: string }> = {
  Common: {
    text: "text-gray-300",
    bg: "bg-gray-500/20",
    border: "border-gray-400/30",
  },
  Rare: {
    text: "text-cyan-300",
    bg: "bg-cyan-500/20",
    border: "border-cyan-400/30",
  },
  Epic: {
    text: "text-purple-300",
    bg: "bg-purple-500/20",
    border: "border-purple-400/30",
  },
  Legendary: {
    text: "text-amber-300",
    bg: "bg-amber-500/20",
    border: "border-amber-400/30",
  },
}

export function AgentSelector({
  selectedAgentId,
  onSelectAgent,
  className,
}: AgentSelectorProps) {
  const { t } = useTranslation()
  const { agents, isLoading } = useAgents()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const selectedAgent = agents.find((a) => a.agent_id === selectedAgentId)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleSelect = (agent: AgentCardData | null) => {
    onSelectAgent(agent)
    setIsOpen(false)
  }

  if (isLoading) {
    return (
      <div
        className={cn(
          "h-14 rounded-xl bg-white/5 border border-white/10 animate-pulse",
          className
        )}
      />
    )
  }

  return (
    <div ref={dropdownRef} className={cn("relative", className)}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "w-full flex items-center justify-between gap-3 px-4 py-3",
          "bg-white/5 border rounded-xl",
          "transition-all duration-300",
          selectedAgent
            ? RARITY_COLORS[selectedAgent.rarity || "Common"].border
            : "border-white/10",
          "hover:bg-white/10 hover:border-cyan-400/30",
          isOpen && "border-cyan-400/50 shadow-[0_0_15px_rgba(0,247,255,0.2)]"
        )}
      >
        <div className="flex items-center gap-3">
          {selectedAgent ? (
            <>
              {/* Agent Avatar */}
              <div
                className={cn(
                  "relative w-10 h-10 rounded-lg overflow-hidden",
                  "bg-gradient-to-b from-slate-700/50 to-slate-800/50",
                  "border",
                  RARITY_COLORS[selectedAgent.rarity || "Common"].border
                )}
              >
                {selectedAgent.robotImage ? (
                  <Image
                    src={selectedAgent.robotImage}
                    alt={selectedAgent.name}
                    fill
                    sizes="40px"
                    className="object-contain p-1"
                  />
                ) : (
                  <Bot className="w-6 h-6 text-white/40 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                )}
              </div>
              {/* Agent Info */}
              <div className="text-left">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "font-semibold",
                      RARITY_COLORS[selectedAgent.rarity || "Common"].text
                    )}
                  >
                    {selectedAgent.name}
                  </span>
                  <span
                    className={cn(
                      "text-xs px-1.5 py-0.5 rounded",
                      RARITY_COLORS[selectedAgent.rarity || "Common"].bg,
                      RARITY_COLORS[selectedAgent.rarity || "Common"].text
                    )}
                  >
                    Lv.{selectedAgent.level || 1}
                  </span>
                </div>
                <span className="text-xs text-white/40">
                  {selectedAgent.rarity || "Common"} • {selectedAgent.total_documents || 0} docs
                </span>
              </div>
            </>
          ) : (
            <>
              <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-cyan-400" />
              </div>
              <div className="text-left">
                <span className="font-medium text-white">{t("chat.selectAgent")}</span>
                <p className="text-xs text-white/40">
                  {t("chat.searchAcross")}
                </p>
              </div>
            </>
          )}
        </div>

        <ChevronDown
          className={cn(
            "w-5 h-5 text-white/50 transition-transform duration-200",
            isOpen && "rotate-180"
          )}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          className={cn(
            "absolute z-50 w-full mt-2",
            "bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-xl",
            "shadow-[0_8px_32px_rgba(0,0,0,0.4),_0_0_20px_rgba(0,247,255,0.1)]",
            "overflow-hidden",
            "animate-in fade-in slide-in-from-top-2 duration-200"
          )}
        >
          {/* "All Agents" Option */}
          <button
            type="button"
            onClick={() => handleSelect(null)}
            className={cn(
              "w-full flex items-center justify-between gap-3 px-4 py-3",
              "hover:bg-white/5 transition-colors",
              !selectedAgentId && "bg-cyan-500/10"
            )}
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-white/10 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-cyan-400" />
              </div>
              <div className="text-left">
                <span className="font-medium text-white">{t("chat.allAgents")}</span>
                <p className="text-xs text-white/40">
                  {t("chat.searchAcross")}
                </p>
              </div>
            </div>
            {!selectedAgentId && <Check className="w-5 h-5 text-cyan-400" />}
          </button>

          <div className="border-t border-white/5" />

          {/* Agent List */}
          <div className="max-h-64 overflow-y-auto custom-scrollbar">
            {agents.map((agent) => {
              const isSelected = agent.agent_id === selectedAgentId
              const rarity = agent.rarity || "Common"
              const colors = RARITY_COLORS[rarity]

              return (
                <button
                  key={agent.agent_id}
                  type="button"
                  onClick={() => handleSelect(agent)}
                  className={cn(
                    "w-full flex items-center justify-between gap-3 px-4 py-3",
                    "hover:bg-white/5 transition-colors",
                    isSelected && colors.bg
                  )}
                >
                  <div className="flex items-center gap-3">
                    {/* Agent Avatar */}
                    <div
                      className={cn(
                        "relative w-10 h-10 rounded-lg overflow-hidden",
                        "bg-gradient-to-b from-slate-700/50 to-slate-800/50",
                        "border",
                        colors.border
                      )}
                    >
                      {agent.robotImage ? (
                        <Image
                          src={agent.robotImage}
                          alt={agent.name}
                          fill
                          sizes="40px"
                          className="object-contain p-1"
                        />
                      ) : (
                        <Bot className="w-6 h-6 text-white/40 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                      )}
                    </div>
                    {/* Agent Info */}
                    <div className="text-left">
                      <div className="flex items-center gap-2">
                        <span className={cn("font-medium", colors.text)}>
                          {agent.name}
                        </span>
                        <span
                          className={cn(
                            "text-xs px-1.5 py-0.5 rounded",
                            colors.bg,
                            colors.text
                          )}
                        >
                          Lv.{agent.level || 1}
                        </span>
                      </div>
                      <span className="text-xs text-white/40">
                        {rarity} • {agent.total_documents || 0} docs •{" "}
                        {(agent.total_queries || 0).toLocaleString()} queries
                      </span>
                    </div>
                  </div>

                  {isSelected && <Check className={cn("w-5 h-5", colors.text)} />}
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
