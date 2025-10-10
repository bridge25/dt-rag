'use client'

import React, { useState } from 'react'
import { Loader2 } from 'lucide-react'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  children: React.ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  children,
  className = '',
  onMouseEnter,
  onMouseLeave,
  ...props
}: ButtonProps) {
  const [isHovered, setIsHovered] = useState(false)

  const baseStyles = 'relative inline-flex items-center justify-center font-medium transition-all duration-normal focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden'

  const variantStyles = {
    primary: 'bg-primary-800 text-white hover:bg-primary-900 focus:ring-primary-500 shadow-elevation-1 hover:shadow-elevation-2',
    secondary: 'bg-accent-600 text-white hover:bg-accent-700 focus:ring-accent-500 shadow-elevation-1 hover:shadow-elevation-2',
    ghost: 'bg-transparent text-primary-800 hover:bg-primary-50 focus:ring-primary-500 border border-primary-300',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 shadow-elevation-1 hover:shadow-elevation-2'
  }

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm rounded-md',
    md: 'px-4 py-2 text-base rounded-md',
    lg: 'px-6 py-3 text-lg rounded-lg'
  }

  const handleMouseEnter = (e: React.MouseEvent<HTMLButtonElement>) => {
    setIsHovered(true)
    onMouseEnter?.(e)
  }

  const handleMouseLeave = (e: React.MouseEvent<HTMLButtonElement>) => {
    setIsHovered(false)
    onMouseLeave?.(e)
  }

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      disabled={disabled || loading}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      {...props}
    >
      {loading && (
        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
      )}

      {children}

      {(variant === 'primary' || variant === 'secondary') && (
        <span
          className={`absolute inset-0 ${
            isHovered ? 'animate-shine' : ''
          } motion-reduce:animate-none`}
          style={{
            background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
            transform: isHovered ? 'translateX(0)' : 'translateX(-100%)',
            pointerEvents: 'none'
          }}
        />
      )}
    </button>
  )
}
