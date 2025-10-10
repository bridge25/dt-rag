"use client"

import React, { useEffect, useState, useCallback } from "react"
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react"

export interface ToastProps {
  id: string
  type?: "success" | "error" | "info" | "warning"
  message: string
  duration?: number
  onClose: (id: string) => void
  showConfetti?: boolean
}

export function Toast({
  id,
  type = "info",
  message,
  duration = 4000,
  onClose,
  showConfetti = false
}: ToastProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [confettiParticles, setConfettiParticles] = useState<Array<{ id: number; x: number; delay: number }>>([])

  const handleClose = useCallback(() => {
    setIsVisible(false)
    setTimeout(() => onClose(id), 300)
  }, [id, onClose])

  useEffect(() => {
    setIsVisible(true)

    if (type === "success" && showConfetti) {
      const particles = Array.from({ length: 30 }, (_, i) => ({
        id: i,
        x: Math.random() * 100,
        delay: Math.random() * 500
      }))
      setConfettiParticles(particles)
    }

    const timer = setTimeout(() => {
      handleClose()
    }, duration)

    return () => clearTimeout(timer)
  }, [duration, type, showConfetti, handleClose])

  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    info: Info,
    warning: AlertTriangle
  }

  const colors = {
    success: "bg-green-50 border-green-200 text-green-800",
    error: "bg-red-50 border-red-200 text-red-800",
    info: "bg-blue-50 border-blue-200 text-blue-800",
    warning: "bg-yellow-50 border-yellow-200 text-yellow-800"
  }

  const iconColors = {
    success: "text-green-500",
    error: "text-red-500",
    info: "text-blue-500",
    warning: "text-yellow-500"
  }

  const Icon = icons[type]

  return (
    <div
      className={`
        relative flex items-center p-4 mb-3 rounded-lg border shadow-elevation-3
        transition-all duration-300 ease-out
        ${colors[type]}
        ${isVisible ? "opacity-100 translate-x-0" : "opacity-0 translate-x-full"}
      `}
      role="alert"
    >
      {confettiParticles.length > 0 && (
        <div className="absolute inset-0 overflow-hidden pointer-events-none motion-reduce:hidden">
          {confettiParticles.map((particle) => (
            <div
              key={particle.id}
              className="absolute w-2 h-2 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full animate-confetti"
              style={{
                left: `${particle.x}%`,
                animationDelay: `${particle.delay}ms`
              }}
            />
          ))}
        </div>
      )}

      <Icon className={`w-5 h-5 mr-3 flex-shrink-0 ${iconColors[type]}`} />

      <div className="flex-1 text-sm font-medium">
        {message}
      </div>

      <button
        onClick={handleClose}
        className="ml-3 flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
        aria-label="Close"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

export interface ToastContainerProps {
  toasts: ToastProps[]
  onRemove: (id: string) => void
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div className="fixed top-4 right-4 z-50 w-full max-w-sm">
      {toasts.map((toast) => (
        <Toast key={toast.id} {...toast} onClose={onRemove} />
      ))}
    </div>
  )
}
