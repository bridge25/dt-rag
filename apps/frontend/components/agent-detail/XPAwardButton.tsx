/**
 * XP Award Button Component
 * Allows awarding XP to agents with different amounts and reasons
 *
 * @CODE:FRONTEND-MIGRATION-002:XP-BUTTON
 */
"use client"

import { useXPAward } from "@/hooks/useXPAward"

interface XPAwardButtonProps {
  agentId: string
  onLevelUp?: (oldLevel: number, newLevel: number) => void
}

interface XPButton {
  label: string
  amount: number
  reason: "chat" | "positive_feedback" | "ragas_bonus"
  className: string
}

const XP_BUTTONS: XPButton[] = [
  {
    label: "Chat Complete (+10 XP)",
    amount: 10,
    reason: "chat",
    className: "bg-blue-600 hover:bg-blue-700",
  },
  {
    label: "Positive Feedback (+50 XP)",
    amount: 50,
    reason: "positive_feedback",
    className: "bg-green-600 hover:bg-green-700",
  },
  {
    label: "RAGAS Bonus (+100 XP)",
    amount: 100,
    reason: "ragas_bonus",
    className: "bg-purple-600 hover:bg-purple-700",
  },
]

export function XPAwardButton({ agentId, onLevelUp }: XPAwardButtonProps) {
  const { mutate, isPending } = useXPAward({
    onSuccess: (data) => {
      if (data.leveled_up && onLevelUp) {
        onLevelUp(data.new_level - 1, data.new_level)
      }
    },
  })

  const handleAwardXP = (
    amount: number,
    reason: "chat" | "positive_feedback" | "ragas_bonus"
  ) => {
    mutate({ agentId, amount, reason })
  }

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-gray-900 mb-3">Award XP</h3>
      <div className="flex flex-col gap-3">
        {XP_BUTTONS.map((button) => (
          <button
            key={button.reason}
            onClick={() => handleAwardXP(button.amount, button.reason)}
            disabled={isPending}
            className={`
              px-6 py-3 text-white rounded-lg font-medium transition-all
              disabled:opacity-50 disabled:cursor-not-allowed
              ${button.className}
            `}
          >
            {isPending ? "Processing..." : button.label}
          </button>
        ))}
      </div>
    </div>
  )
}
