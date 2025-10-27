"use client"

import React from "react"

export interface GridProps {
  children: React.ReactNode
  gap?: "xs" | "sm" | "md" | "lg" | "xl"
  className?: string
}

export function Grid({ children, gap = "md", className = "" }: GridProps) {
  const gapClasses = {
    xs: "gap-1",
    sm: "gap-2",
    md: "gap-4",
    lg: "gap-6",
    xl: "gap-8"
  }

  return (
    <div className={`grid grid-cols-12 ${gapClasses[gap]} ${className}`}>
      {children}
    </div>
  )
}

export interface GridItemProps {
  children: React.ReactNode
  colSpan?: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12
  className?: string
}

export function GridItem({ children, colSpan = 12, className = "" }: GridItemProps) {
  const colSpanClasses = {
    1: "col-span-1",
    2: "col-span-2",
    3: "col-span-3",
    4: "col-span-4",
    5: "col-span-5",
    6: "col-span-6",
    7: "col-span-7",
    8: "col-span-8",
    9: "col-span-9",
    10: "col-span-10",
    11: "col-span-11",
    12: "col-span-12"
  }

  return (
    <div className={`${colSpanClasses[colSpan]} ${className}`}>
      {children}
    </div>
  )
}
