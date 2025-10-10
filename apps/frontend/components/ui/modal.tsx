'use client'

import React, { useEffect } from 'react'
import { createPortal } from 'react-dom'
import FocusLock from 'react-focus-lock'
import { X } from 'lucide-react'

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
}

export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  useEffect(() => {
    if (!isOpen) return

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  if (!isOpen) return null
  if (typeof window === 'undefined') return null

  return createPortal(
    <FocusLock>
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
          data-testid="modal-backdrop"
        />
        <div className="relative z-10 bg-white rounded-lg shadow-elevation-3 max-w-lg w-full mx-4 p-6">
          <div className="flex items-center justify-between mb-4">
            {title && <h2 className="text-2xl font-bold">{title}</h2>}
            <button
              onClick={onClose}
              className="ml-auto text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <div>{children}</div>
        </div>
      </div>
    </FocusLock>,
    document.body
  )
}
