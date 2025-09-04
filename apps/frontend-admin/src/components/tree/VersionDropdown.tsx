'use client'

import React from 'react'
import { ChevronDown } from 'lucide-react'

interface VersionDropdownProps {
  versions: string[]
  currentVersion: string
  onVersionChange: (version: string) => void
  loading?: boolean
}

export function VersionDropdown({
  versions,
  currentVersion,
  onVersionChange,
  loading = false
}: VersionDropdownProps) {
  return (
    <div className="mb-6">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Taxonomy Version
      </label>
      <div className="relative">
        <select
          value={currentVersion}
          onChange={(e) => onVersionChange(e.target.value)}
          disabled={loading}
          className="w-full appearance-none bg-white border border-gray-300 rounded-md px-4 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed"
        >
          {versions.map((version) => (
            <option key={version} value={version}>
              {version}
            </option>
          ))}
        </select>
        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          <ChevronDown className="h-4 w-4 text-gray-400" />
        </div>
      </div>
    </div>
  )
}