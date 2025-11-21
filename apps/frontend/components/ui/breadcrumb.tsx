/**
 * Breadcrumb navigation component
 *
 * @CODE:UI-001
 */

"use client"

import React from "react"
import { ChevronRight } from "lucide-react"

export interface BreadcrumbItem {
  label: string
  href: string
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[]
}

export function Breadcrumb({ items }: BreadcrumbProps) {
  const displayItems = React.useMemo(() => {
    if (items.length <= 3) {
      return items
    }

    return [
      items[0],
      { label: "...", href: "#" },
      items[items.length - 1]
    ]
  }, [items])

  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex items-center space-x-2 text-sm">
        {displayItems.map((item, index) => {
          const isLast = index === displayItems.length - 1
          const isEllipsis = item.label === "..."

          return (
            <li key={`${item.href}-${index}`} className="flex items-center">
              {isLast ? (
                <span className="font-bold text-gray-900">
                  {item.label}
                </span>
              ) : isEllipsis ? (
                <span className="text-gray-500">
                  {item.label}
                </span>
              ) : (
                <a
                  href={item.href}
                  className="text-gray-600 hover:text-gray-900 transition-colors"
                >
                  {item.label}
                </a>
              )}
              {!isLast && (
                <ChevronRight className="w-4 h-4 mx-2 text-gray-400" />
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
