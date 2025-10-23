"use client"

import React from "react"
import { AlertCircle, CheckCircle } from "lucide-react"

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  helperText?: string
  state?: "default" | "error" | "success"
  icon?: React.ReactNode
  iconPosition?: "left" | "right"
}

export function Input({
  label,
  helperText,
  state = "default",
  icon,
  iconPosition = "left",
  className = "",
  id,
  ...props
}: InputProps) {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`

  const baseStyles = "w-full px-4 py-2 text-base border rounded-md transition-all duration-normal focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"

  const stateStyles = {
    default: "border-gray-300 focus:border-accent-500 focus:ring-2 focus:ring-accent-500 focus:ring-offset-2 motion-reduce:focus:ring-offset-0",
    error: "border-red-500 focus:border-red-500 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 motion-reduce:focus:ring-offset-0 text-red-900",
    success: "border-green-500 focus:border-green-500 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 motion-reduce:focus:ring-offset-0 text-green-900"
  }

  const getStateIcon = () => {
    if (state === "error") return <AlertCircle className="w-5 h-5 text-red-500" />
    if (state === "success") return <CheckCircle className="w-5 h-5 text-green-500" />
    return null
  }

  const stateIcon = getStateIcon()
  const displayIcon = stateIcon || icon

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          {label}
        </label>
      )}

      <div className="relative">
        {displayIcon && iconPosition === "left" && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
            {displayIcon}
          </div>
        )}

        <input
          id={inputId}
          className={`
            ${baseStyles}
            ${stateStyles[state]}
            ${displayIcon && iconPosition === "left" ? "pl-11" : ""}
            ${displayIcon && iconPosition === "right" ? "pr-11" : ""}
            ${className}
          `}
          {...props}
        />

        {displayIcon && iconPosition === "right" && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
            {displayIcon}
          </div>
        )}
      </div>

      {helperText && (
        <p
          className={`mt-2 text-sm ${
            state === "error" ? "text-red-600" :
            state === "success" ? "text-green-600" :
            "text-gray-600"
          }`}
        >
          {helperText}
        </p>
      )}
    </div>
  )
}
