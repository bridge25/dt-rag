"use client"

/**
 * LevelUpModal Component
 * Uses framer-motion and react-confetti for celebration effects
 * @CODE:FRONTEND-MIGRATION-001
 */

import { useEffect } from "react"
import dynamic from "next/dynamic"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import type { Rarity } from "./types"

// Dynamic import for SSR-incompatible library
const Confetti = dynamic(() => import("react-confetti"), {
  ssr: false,
  loading: () => null,
})

interface LevelUpModalProps {
  isOpen: boolean
  onClose: () => void
  oldLevel: number
  newLevel: number
  rarity: Rarity
  upgradeRarity?: Rarity
}

const backdropVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
}

const modalVariants = {
  hidden: { scale: 0.8, opacity: 0 },
  visible: {
    scale: 1,
    opacity: 1,
    transition: {
      type: "spring" as const,
      stiffness: 300,
      damping: 25,
    },
  },
  exit: {
    scale: 0.8,
    opacity: 0,
    transition: {
      duration: 0.2,
    },
  },
}

export function LevelUpModal({
  isOpen,
  onClose,
  oldLevel,
  newLevel,
  rarity,
  upgradeRarity,
}: LevelUpModalProps) {
  useEffect(() => {
    if (!isOpen) return

    const timer = setTimeout(() => {
      onClose()
    }, 3000)

    return () => {
      clearTimeout(timer)
    }
  }, [isOpen, onClose])

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <Confetti numberOfPieces={200} recycle={false} gravity={0.3} />

          <motion.div
            data-testid="modal-backdrop"
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            onClick={onClose}
          >
            <motion.div
              role="dialog"
              aria-labelledby="level-up-title"
              aria-modal="true"
              className="bg-white rounded-lg p-8 max-w-md w-full mx-4 shadow-2xl"
              variants={modalVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={(e) => e.stopPropagation()}
            >
              <h2
                id="level-up-title"
                className="text-3xl font-bold text-center mb-6 text-gray-900"
              >
                Level Up!
              </h2>

              <div className="flex items-center justify-center gap-4 mb-6">
                <div className="text-center">
                  <div className="text-4xl font-bold text-gray-700">
                    Lv.{oldLevel}
                  </div>
                </div>
                <div className="text-4xl text-gray-400 font-bold">→</div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-green-600">
                    Lv.{newLevel}
                  </div>
                </div>
              </div>

              {upgradeRarity && (
                <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg">
                  <p className="text-center font-semibold text-gray-900 mb-2">
                    Rarity Upgrade!
                  </p>
                  <div className="flex items-center justify-center gap-3">
                    <span
                      className={cn(
                        "font-bold",
                        rarity === "Common" && "text-gray-600",
                        rarity === "Rare" && "text-blue-600",
                        rarity === "Epic" && "text-purple-600",
                        rarity === "Legendary" && "text-amber-500"
                      )}
                    >
                      {rarity}
                    </span>
                    <span className="text-gray-400">→</span>
                    <span
                      className={cn(
                        "font-bold",
                        upgradeRarity === "Common" && "text-gray-600",
                        upgradeRarity === "Rare" && "text-blue-600",
                        upgradeRarity === "Epic" && "text-purple-600",
                        upgradeRarity === "Legendary" && "text-amber-500"
                      )}
                    >
                      {upgradeRarity}
                    </span>
                  </div>
                </div>
              )}

              {!upgradeRarity && (
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-1">Rarity</p>
                  <p
                    className={cn(
                      "text-xl font-bold",
                      rarity === "Common" && "text-gray-600",
                      rarity === "Rare" && "text-blue-600",
                      rarity === "Epic" && "text-purple-600",
                      rarity === "Legendary" && "text-amber-500"
                    )}
                  >
                    {rarity}
                  </p>
                </div>
              )}
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
