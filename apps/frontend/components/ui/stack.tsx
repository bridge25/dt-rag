"use client"

import React from "react"

export interface StackProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  direction?: "vertical" | "horizontal"
  spacing?: "xs" | "sm" | "md" | "lg" | "xl"
  align?: "start" | "center" | "end" | "stretch"
  justify?: "start" | "center" | "end" | "between" | "around"
  className?: string
}

export function Stack({
  children,
  direction = "vertical",
  spacing = "md",
  align,
  justify,
  className = "",
  ...props
}: StackProps) {
  const directionClasses = {
    vertical: "flex-col",
    horizontal: "flex-row"
  }

  const spacingClasses = {
    xs: "gap-1",
    sm: "gap-2",
    md: "gap-4",
    lg: "gap-6",
    xl: "gap-8"
  }

  const alignClasses = {
    start: "items-start",
    center: "items-center",
    end: "items-end",
    stretch: "items-stretch"
  }

  const justifyClasses = {
    start: "justify-start",
    center: "justify-center",
    end: "justify-end",
    between: "justify-between",
    around: "justify-around"
  }

  return (
    <div
      className={`
        flex
        ${directionClasses[direction]}
        ${spacingClasses[spacing]}
        ${align ? alignClasses[align] : ""}
        ${justify ? justifyClasses[justify] : ""}
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  )
}
