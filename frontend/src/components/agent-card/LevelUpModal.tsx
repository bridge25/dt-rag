// @CODE:AGENT-CARD-001-ANIM-001
// @CODE:TAILWIND-V4-COMPLETE-001-JIT-FIX-MODAL
import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Confetti from 'react-confetti'
import type { Rarity } from '@/lib/api/types'
import { cn } from '@/lib/utils'

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
      type: 'spring',
      stiffness: 300,
      damping: 25,
    }
  },
  exit: {
    scale: 0.8,
    opacity: 0,
    transition: {
      duration: 0.2,
    }
  },
}

export function LevelUpModal({
  isOpen,
  onClose,
  oldLevel,
  newLevel,
  rarity,
  upgradeRarity
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
          {/* Confetti Effect */}
          <Confetti
            numberOfPieces={200}
            recycle={false}
            gravity={0.3}
          />

          {/* Backdrop */}
          <motion.div
            data-testid="modal-backdrop"
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            onClick={onClose}
          >
            {/* Modal Content */}
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
              {/* Title */}
              <h2
                id="level-up-title"
                className="text-3xl font-bold text-center mb-6 text-gray-900"
              >
                Level Up!
              </h2>

              {/* Level Progression */}
              <div className="flex items-center justify-center gap-4 mb-6">
                <div className="text-center">
                  <div className="text-4xl font-bold text-gray-700">
                    Lv.{oldLevel}
                  </div>
                </div>

                <div className="text-4xl text-gray-400 font-bold">
                  →
                </div>

                <div className="text-center">
                  <div className="text-4xl font-bold text-green-600">
                    Lv.{newLevel}
                  </div>
                </div>
              </div>

              {/* Rarity Upgrade (if applicable) */}
              {upgradeRarity && (
                <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg">
                  <p className="text-center font-semibold text-gray-900 mb-2">
                    Rarity Upgrade!
                  </p>
                  <div className="flex items-center justify-center gap-3">
                    <span className={cn(
                      'font-bold',
                      rarity === 'Common' && 'text-gray-600',
                      rarity === 'Rare' && 'text-blue-600',
                      rarity === 'Epic' && 'text-purple-600',
                      rarity === 'Legendary' && 'text-accent-gold-500'
                    )}>
                      {rarity}
                    </span>
                    <span className="text-gray-400">→</span>
                    <span className={cn(
                      'font-bold',
                      upgradeRarity === 'Common' && 'text-gray-600',
                      upgradeRarity === 'Rare' && 'text-blue-600',
                      upgradeRarity === 'Epic' && 'text-purple-600',
                      upgradeRarity === 'Legendary' && 'text-accent-gold-500'
                    )}>
                      {upgradeRarity}
                    </span>
                  </div>
                </div>
              )}

              {/* Current Rarity Display (if no upgrade) */}
              {!upgradeRarity && (
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-1">Rarity</p>
                  <p className={cn(
                    'text-xl font-bold',
                    rarity === 'Common' && 'text-gray-600',
                    rarity === 'Rare' && 'text-blue-600',
                    rarity === 'Epic' && 'text-purple-600',
                    rarity === 'Legendary' && 'text-accent-gold-500'
                  )}>
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
