"use client"

import React, { createContext, useContext, useState } from "react"

interface TabsContextType {
  value: string
  onValueChange: (_value: string) => void
}

const TabsContext = createContext<TabsContextType | undefined>(undefined)

function useTabsContext() {
  const context = useContext(TabsContext)
  if (!context) {
    throw new Error("Tabs components must be used within a Tabs component")
  }
  return context
}

export interface TabsProps {
  children: React.ReactNode
  defaultValue?: string
  value?: string
  onValueChange?: (_value: string) => void
}

export function Tabs({ children, defaultValue, value, onValueChange }: TabsProps) {
  const [internalValue, setInternalValue] = useState(defaultValue || "")

  const currentValue = value !== undefined ? value : internalValue
  const handleValueChange = onValueChange || setInternalValue

  return (
    <TabsContext.Provider value={{ value: currentValue, onValueChange: handleValueChange }}>
      <div>{children}</div>
    </TabsContext.Provider>
  )
}

export interface TabListProps {
  children: React.ReactNode
}

export function TabList({ children }: TabListProps) {
  return (
    <div className="flex border-b border-gray-200" role="tablist">
      {children}
    </div>
  )
}

export interface TabProps {
  children: React.ReactNode
  value: string
}

export function Tab({ children, value }: TabProps) {
  const { value: currentValue, onValueChange } = useTabsContext()
  const isActive = currentValue === value

  return (
    <button
      role="tab"
      aria-selected={isActive}
      onClick={() => onValueChange(value)}
      className={`
        px-4 py-2 -mb-px border-b-2 font-medium transition-all duration-normal
        ${
          isActive
            ? "border-accent-600 text-accent-600"
            : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
        }
      `}
    >
      {children}
    </button>
  )
}

export interface TabPanelProps {
  children: React.ReactNode
  value: string
}

export function TabPanel({ children, value }: TabPanelProps) {
  const { value: currentValue } = useTabsContext()

  if (currentValue !== value) {
    return null
  }

  return (
    <div role="tabpanel" className="py-4">
      {children}
    </div>
  )
}
