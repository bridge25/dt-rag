'use client'

import { TaxonomyVersion } from '@/services/taxonomyService'

interface VersionDropdownProps {
  versions: TaxonomyVersion[]
  currentVersion: string
  onVersionChange: (version: string) => void
  className?: string
}

export default function VersionDropdown({
  versions,
  currentVersion,
  onVersionChange,
  className = ''
}: VersionDropdownProps) {
  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      <label className="text-sm font-medium text-gray-700">
        Taxonomy Version:
      </label>
      <select
        value={currentVersion}
        onChange={(e) => onVersionChange(e.target.value)}
        className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        {versions.map((version) => (
          <option key={version.version} value={version.version}>
            {version.version} ({version.node_count} nodes)
          </option>
        ))}
      </select>
      {versions.length > 0 && (
        <div className="text-xs text-gray-500">
          Created: {new Date(versions.find(v => v.version === currentVersion)?.created_at || '').toLocaleDateString()}
        </div>
      )}
    </div>
  )
}
