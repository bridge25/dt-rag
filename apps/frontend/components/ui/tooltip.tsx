"use client"

import React, { useState, useRef, useEffect } from "react"
import { createPortal } from "react-dom"

export interface TooltipProps {
  content: string
  children: React.ReactElement
  position?: "top" | "bottom" | "left" | "right"
  delay?: number
}

export function Tooltip({ content, children, position = "top", delay = 200 }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [coords, setCoords] = useState({ x: 0, y: 0 })
  const triggerRef = useRef<HTMLElement>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>()

  const handleMouseEnter = () => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true)
      updatePosition()
    }, delay)
  }

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setIsVisible(false)
  }

  const updatePosition = () => {
    if (!triggerRef.current) return

    const rect = triggerRef.current.getBoundingClientRect()
    const offset = 8

    const positions = {
      top: {
        x: rect.left + rect.width / 2,
        y: rect.top - offset
      },
      bottom: {
        x: rect.left + rect.width / 2,
        y: rect.bottom + offset
      },
      left: {
        x: rect.left - offset,
        y: rect.top + rect.height / 2
      },
      right: {
        x: rect.right + offset,
        y: rect.top + rect.height / 2
      }
    }

    setCoords(positions[position])
  }

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  const positionClasses = {
    top: "-translate-x-1/2 -translate-y-full",
    bottom: "-translate-x-1/2",
    left: "-translate-x-full -translate-y-1/2",
    right: "-translate-y-1/2"
  }

  const clonedChild = React.cloneElement(children, {
    ref: triggerRef,
    onMouseEnter: handleMouseEnter,
    onMouseLeave: handleMouseLeave
  })

  return (
    <>
      {clonedChild}
      {isVisible && typeof window !== "undefined" && createPortal(
        <div
          className={`
            fixed z-50 px-2 py-1 text-xs font-medium text-white bg-gray-900 rounded
            pointer-events-none transition-opacity duration-fast
            ${positionClasses[position]}
          `}
          style={{
            left: `${coords.x}px`,
            top: `${coords.y}px`
          }}
        >
          {content}
        </div>,
        document.body
      )}
    </>
  )
}
