"use client"

/**
 * AgentCard Component - Ethereal Glass Design
 * Matches 뉴디자인1 design exactly:
 * - Large robot image (60-70% of card)
 * - Cyan progress bar below robot
 * - Stats section at bottom
 * @CODE:FRONTEND-REDESIGN-001-AGENT-CARD
 */

import { memo } from "react"
import Image from "next/image"
import { cn } from "@/lib/utils"
import type { AgentCardData } from "./types"

interface AgentCardProps {
  agent: AgentCardData
  className?: string
}

const arePropsEqual = (
  prevProps: AgentCardProps,
  nextProps: AgentCardProps
) => {
  return (
    prevProps.agent.agent_id === nextProps.agent.agent_id &&
    prevProps.agent.progress === nextProps.agent.progress &&
    prevProps.className === nextProps.className
  )
}

export const AgentCard = memo<AgentCardProps>(function AgentCard({
  agent,
  className,
}) {
  // Format currency values
  const formatCurrency = (value: number) => {
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}k`
    }
    return `$${value.toLocaleString()}`
  }

  // Format numbers with thousands separator
  const formatNumber = (value: number) => {
    return value.toLocaleString()
  }

  // Format growth percentage
  const formatGrowth = (value: number) => {
    const sign = value >= 0 ? "+" : ""
    return `${sign}${value}%`
  }

  return (
    <div
      className={cn(
        // Gemini Glassmorphism Guide 적용
        "group relative w-full h-full rounded-2xl p-4 overflow-hidden",
        // Glass morphism - bg-white/5 backdrop-blur-lg
        "bg-white/5 backdrop-blur-lg",
        "border border-white/10",
        "flex flex-col gap-3",
        // 복합 글로우 기본
        "shadow-[0_4px_15px_rgba(0,0,0,0.2)]",
        // Hover: 네온 글로우 강화
        "transition-all duration-300",
        "hover:border-cyan-400/50",
        "hover:shadow-[0_4px_20px_rgba(0,0,0,0.3),_0_0_25px_rgba(0,247,255,0.8)]",
        className
      )}
      role="article"
      aria-label={`${agent.name} agent card`}
    >
      {/* Robot Image Container - 60-70% of card */}
      {/* 뉴디자인1: rembg로 배경 제거된 투명 PNG 사용 */}
      <div className="relative flex justify-center items-center w-full aspect-square rounded-xl bg-gradient-to-b from-slate-800/40 to-slate-900/60 border border-white/10 overflow-hidden">
        {agent.robotImage ? (
          <Image
            src={agent.robotImage}
            alt={agent.name}
            fill
            sizes="(max-width: 768px) 50vw, 20vw"
            // 투명 PNG: mix-blend-mode 불필요, drop-shadow로 네온 글로우 강화
            className="object-contain p-3 drop-shadow-[0_0_20px_rgba(0,247,255,0.6)] transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-white/40 text-sm">
            {agent.name}
          </div>
        )}
      </div>

      {/* Cyan Progress Bar */}
      <div className="w-full h-1 rounded-full bg-slate-600/50 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-blue-400 shadow-[0_0_10px_rgba(34,211,238,0.6)] transition-all duration-300"
          style={{
            width: `${Math.min(Math.max(agent.progress || 0, 0), 100)}%`,
          }}
          role="progressbar"
          aria-valuenow={agent.progress || 0}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>

      {/* Stats Section */}
      <div className="space-y-2">
        {/* Users */}
        <div className="flex justify-between items-center text-sm">
          <span className="text-white/60">Users:</span>
          <span className="text-white font-medium">{formatNumber(agent.stats.users)}</span>
        </div>

        {/* Robos */}
        <div className="flex justify-between items-center text-sm">
          <span className="text-white/60">Robos:</span>
          <span className="text-white font-medium">{formatCurrency(agent.stats.robos)}</span>
        </div>

        {/* Revenue */}
        <div className="flex justify-between items-center text-sm">
          <span className="text-white/60">Revenue:</span>
          <span className="text-white font-medium">{formatCurrency(agent.stats.revenue)}</span>
        </div>

        {/* Growth - Gemini Guide: 네온 글로우 텍스트 */}
        <div className="flex justify-between items-center text-sm">
          <span className="text-white/60">Growth:</span>
          <span className="text-cyan-400 font-medium drop-shadow-[0_0_5px_rgba(0,247,255,0.7)]">
            {formatGrowth(agent.stats.growth)}
          </span>
        </div>
      </div>

      {/* Gemini Guide: 하단 장식 바 - 네온 그라데이션 라인 */}
      <div
        className={cn(
          "absolute bottom-0 left-0 w-full h-0.5",
          "bg-gradient-to-r from-transparent via-cyan-400/70 to-transparent",
          "opacity-60 group-hover:opacity-100 transition-opacity duration-300"
        )}
      />
    </div>
  )
}, arePropsEqual)
