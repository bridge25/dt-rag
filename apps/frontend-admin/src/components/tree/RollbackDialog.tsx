'use client'

import { useState } from 'react'
import { TaxonomyVersion } from '@/services/taxonomyService'

interface RollbackDialogProps {
  isOpen: boolean
  currentVersion: string
  targetVersion: TaxonomyVersion | null
  onConfirm: (reason: string, performedBy: string) => void
  onCancel: () => void
  className?: string
}

export default function RollbackDialog({
  isOpen,
  currentVersion,
  targetVersion,
  onConfirm,
  onCancel,
  className = ''
}: RollbackDialogProps) {
  const [reason, setReason] = useState('')
  const [performedBy, setPerformedBy] = useState('')

  if (!isOpen || !targetVersion) return null

  const handleConfirm = () => {
    if (!reason.trim() || !performedBy.trim()) {
      alert('Please provide both reason and performer name')
      return
    }
    onConfirm(reason, performedBy)
    setReason('')
    setPerformedBy('')
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className={`bg-white rounded-lg shadow-xl max-w-md w-full mx-4 ${className}`}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-bold text-gray-900">⚠️ Confirm Rollback</h3>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-4">
          {/* Warning */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-800">
              <strong>Warning:</strong> This will rollback the taxonomy from version{' '}
              <code className="bg-yellow-100 px-1 rounded">{currentVersion}</code> to{' '}
              <code className="bg-yellow-100 px-1 rounded">{targetVersion.version}</code>.
            </p>
          </div>

          {/* Version Info */}
          <div className="space-y-2">
            <div className="text-sm">
              <span className="text-gray-600">Target Version:</span>
              <span className="ml-2 font-medium">{targetVersion.version}</span>
            </div>
            <div className="text-sm">
              <span className="text-gray-600">Node Count:</span>
              <span className="ml-2 font-medium">{targetVersion.node_count} nodes</span>
            </div>
            <div className="text-sm">
              <span className="text-gray-600">Created:</span>
              <span className="ml-2 font-medium">
                {new Date(targetVersion.created_at).toLocaleString()}
              </span>
            </div>
          </div>

          {/* Reason Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Rollback Reason <span className="text-red-500">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Explain why this rollback is necessary..."
              required
            />
          </div>

          {/* Performer Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Performed By <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={performedBy}
              onChange={(e) => setPerformedBy(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Your name or ID..."
              required
            />
          </div>

          {/* TTR Notice */}
          <div className="text-xs text-gray-500">
            <p>✓ Target TTR (Time To Recover): ≤ 15 minutes</p>
            <p>✓ Audit log will be automatically created</p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            Confirm Rollback
          </button>
        </div>
      </div>
    </div>
  )
}
