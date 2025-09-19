// Simple UI components for the DT-RAG system
// These are basic implementations - in a real production app you might use a library like Radix UI

import React, { forwardRef } from 'react'
import { cn } from '@/lib/utils'

// Button Component
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
  size?: 'default' | 'sm' | 'lg'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        className={cn(
          'btn',
          {
            'btn-default': variant === 'default',
            'btn-destructive': variant === 'destructive',
            'btn-outline': variant === 'outline',
            'btn-secondary': variant === 'secondary',
            'btn-ghost': variant === 'ghost',
            'btn-link': variant === 'link',
            'btn-sm': size === 'sm',
            'btn-lg': size === 'lg',
          },
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

// Input Component
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => {
    return (
      <input
        className={cn('input', className)}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = 'Input'

// Label Component
interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {}

export const Label = forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, ...props }, ref) => {
    return (
      <label
        className={cn('text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70', className)}
        ref={ref}
        {...props}
      />
    )
  }
)
Label.displayName = 'Label'

// Checkbox Component
interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onCheckedChange?: (checked: boolean) => void
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, onCheckedChange, onChange, ...props }, ref) => {
    return (
      <input
        type="checkbox"
        className={cn('h-4 w-4 rounded border border-primary text-primary focus:ring-2 focus:ring-primary', className)}
        ref={ref}
        onChange={(e) => {
          onChange?.(e)
          onCheckedChange?.(e.target.checked)
        }}
        {...props}
      />
    )
  }
)
Checkbox.displayName = 'Checkbox'

// Slider Component
interface SliderProps {
  value: number[]
  min?: number
  max?: number
  step?: number
  onValueChange?: (value: number[]) => void
  className?: string
}

export const Slider: React.FC<SliderProps> = ({
  value,
  min = 0,
  max = 100,
  step = 1,
  onValueChange,
  className
}) => {
  return (
    <div className={cn('relative flex items-center w-full', className)}>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value[0]}
        onChange={(e) => onValueChange?.([parseFloat(e.target.value), value[1] || max])}
        className="w-full h-2 bg-accent rounded-lg appearance-none cursor-pointer"
      />
      {value.length > 1 && (
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value[1]}
          onChange={(e) => onValueChange?.([value[0] || min, parseFloat(e.target.value)])}
          className="absolute w-full h-2 bg-accent rounded-lg appearance-none cursor-pointer"
        />
      )}
    </div>
  )
}