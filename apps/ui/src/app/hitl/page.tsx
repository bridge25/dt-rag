'use client'

import React, { useEffect, useState } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { HITLQueue } from '@/components/hitl/HITLQueue'
import { ClassificationQueueItem, BatchOperation } from '@/types/taxonomy'

// Mock data - in real app, this would come from API
const mockQueueItems: ClassificationQueueItem[] = [
  {
    id: 'item_001',
    text: 'This document discusses advanced machine learning algorithms for classification tasks, including support vector machines, random forests, and neural networks. The paper provides comprehensive comparisons of different approaches.',
    suggested_path: ['AI', 'Machine Learning', 'Classification'],
    confidence: 0.85,
    status: 'pending',
    created_at: '2025-09-17T10:30:00Z'
  },
  {
    id: 'item_002',
    text: 'Hierarchical taxonomy structures enable better organization of knowledge domains. This research examines various approaches to building and maintaining taxonomies.',
    suggested_path: ['AI', 'Taxonomy', 'Hierarchical'],
    confidence: 0.92,
    status: 'pending',
    created_at: '2025-09-17T09:15:00Z'
  },
  {
    id: 'item_003',
    text: 'Retrieval-augmented generation systems combine information retrieval with natural language generation to produce more accurate and contextual responses.',
    suggested_path: ['AI', 'RAG', 'Dynamic'],
    confidence: 0.78,
    status: 'pending',
    created_at: '2025-09-17T08:45:00Z'
  },
  {
    id: 'item_004',
    text: 'Clustering algorithms group similar data points together without predefined labels. K-means, hierarchical clustering, and DBSCAN are popular methods.',
    suggested_path: ['AI', 'Machine Learning', 'Clustering'],
    confidence: 0.89,
    status: 'approved',
    created_at: '2025-09-16T16:20:00Z',
    reviewed_at: '2025-09-17T08:00:00Z',
    human_reviewer: 'admin@example.com'
  },
  {
    id: 'item_005',
    text: 'This paper explores general artificial intelligence concepts and their applications in various domains including healthcare, finance, and education.',
    suggested_path: ['AI', 'Machine Learning'],
    confidence: 0.65,
    status: 'rejected',
    created_at: '2025-09-16T14:10:00Z',
    reviewed_at: '2025-09-17T07:30:00Z',
    human_reviewer: 'admin@example.com',
    reason: 'Should be classified under AI > General, not Machine Learning'
  },
  {
    id: 'item_006',
    text: 'Advanced neural network architectures for computer vision tasks including convolutional neural networks, transformers, and attention mechanisms.',
    suggested_path: ['AI', 'Machine Learning', 'Deep Learning'],
    confidence: 0.58,
    status: 'pending',
    created_at: '2025-09-17T07:00:00Z'
  }
]

export default function HITLPage() {
  const [queueItems, setQueueItems] = useState<ClassificationQueueItem[]>(mockQueueItems)

  const handleApprove = (itemId: string, correction?: string) => {
    setQueueItems(prev =>
      prev.map(item =>
        item.id === itemId
          ? {
              ...item,
              status: 'approved' as const,
              reviewed_at: new Date().toISOString(),
              human_reviewer: 'admin@example.com',
              correction
            }
          : item
      )
    )
    console.log('Approved item:', itemId, correction ? `with correction: ${correction}` : '')
  }

  const handleReject = (itemId: string, reason: string) => {
    setQueueItems(prev =>
      prev.map(item =>
        item.id === itemId
          ? {
              ...item,
              status: 'rejected' as const,
              reviewed_at: new Date().toISOString(),
              human_reviewer: 'admin@example.com',
              reason
            }
          : item
      )
    )
    console.log('Rejected item:', itemId, 'reason:', reason)
  }

  const handleBatchOperation = (operation: BatchOperation) => {
    console.log('Batch operation:', operation)

    if (operation.type === 'approve_all') {
      setQueueItems(prev =>
        prev.map(item =>
          operation.items.includes(item.id)
            ? {
                ...item,
                status: 'approved' as const,
                reviewed_at: new Date().toISOString(),
                human_reviewer: operation.reviewer
              }
            : item
        )
      )
    } else if (operation.type === 'reject_all') {
      setQueueItems(prev =>
        prev.map(item =>
          operation.items.includes(item.id)
            ? {
                ...item,
                status: 'rejected' as const,
                reviewed_at: new Date().toISOString(),
                human_reviewer: operation.reviewer,
                reason: operation.notes || 'Batch rejection'
              }
            : item
        )
      )
    } else if (operation.type === 'approve_high_confidence') {
      setQueueItems(prev =>
        prev.map(item =>
          operation.items.includes(item.id) && item.confidence >= 0.8
            ? {
                ...item,
                status: 'approved' as const,
                reviewed_at: new Date().toISOString(),
                human_reviewer: operation.reviewer
              }
            : item
        )
      )
    }
  }

  const pendingCount = queueItems.filter(item => item.status === 'pending').length
  const approvedCount = queueItems.filter(item => item.status === 'approved').length
  const rejectedCount = queueItems.filter(item => item.status === 'rejected').length
  const modifiedCount = queueItems.filter(item => item.status === 'modified').length

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Human-in-the-Loop Queue</h1>
            <p className="text-muted-foreground">
              Review and approve AI-generated document classifications to improve system accuracy.
            </p>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <div className="card-content p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Pending Review</p>
                  <p className="text-2xl font-bold text-yellow-600">{pendingCount}</p>
                </div>
                <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <span className="text-yellow-600 text-sm font-medium">⏳</span>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-content p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Approved</p>
                  <p className="text-2xl font-bold text-green-600">{approvedCount}</p>
                </div>
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 text-sm font-medium">✓</span>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-content p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Rejected</p>
                  <p className="text-2xl font-bold text-red-600">{rejectedCount}</p>
                </div>
                <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                  <span className="text-red-600 text-sm font-medium">✗</span>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-content p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Modified</p>
                  <p className="text-2xl font-bold text-blue-600">{modifiedCount}</p>
                </div>
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 text-sm font-medium">✎</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <HITLQueue
          queueItems={queueItems}
          onApprove={handleApprove}
          onReject={handleReject}
          onBatchOperation={handleBatchOperation}
        />
      </div>
    </AppLayout>
  )
}