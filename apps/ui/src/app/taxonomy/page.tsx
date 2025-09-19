'use client'

import React, { useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { TreePanel } from '@/components/tree/TreePanel'
import { useTaxonomyStore } from '@/stores/taxonomy-store'
import { TaxonomyTree } from '@/types/taxonomy'

// Mock data - in real app, this would come from API
const mockTaxonomyTree: TaxonomyTree = {
  version: "1.8.1",
  total_nodes: 1247,
  total_documents: 8934,
  total_edges: 1246,
  nodes: [
    {
      node_id: "ai_root_001",
      label: "AI",
      canonical_path: ["AI"],
      version: "1.8.1",
      confidence: 1.0,
      document_count: 3241,
      description: "Artificial Intelligence and related technologies"
    },
    {
      node_id: "ai_ml_001",
      label: "Machine Learning",
      canonical_path: ["AI", "Machine Learning"],
      version: "1.8.1",
      confidence: 0.95,
      document_count: 1567,
      description: "Machine learning algorithms and techniques"
    },
    {
      node_id: "ai_ml_classification_001",
      label: "Classification",
      canonical_path: ["AI", "Machine Learning", "Classification"],
      version: "1.8.1",
      confidence: 0.92,
      document_count: 423,
      description: "Classification algorithms and methods"
    },
    {
      node_id: "ai_ml_clustering_001",
      label: "Clustering",
      canonical_path: ["AI", "Machine Learning", "Clustering"],
      version: "1.8.1",
      confidence: 0.89,
      document_count: 312,
      description: "Clustering algorithms and techniques"
    },
    {
      node_id: "ai_rag_001",
      label: "RAG",
      canonical_path: ["AI", "RAG"],
      version: "1.8.1",
      confidence: 0.97,
      document_count: 892,
      description: "Retrieval-Augmented Generation systems"
    },
    {
      node_id: "ai_rag_dynamic_001",
      label: "Dynamic",
      canonical_path: ["AI", "RAG", "Dynamic"],
      version: "1.8.1",
      confidence: 0.94,
      document_count: 234,
      description: "Dynamic taxonomy systems"
    },
    {
      node_id: "ai_rag_static_001",
      label: "Static",
      canonical_path: ["AI", "RAG", "Static"],
      version: "1.8.1",
      confidence: 0.91,
      document_count: 156,
      description: "Static taxonomy systems"
    },
    {
      node_id: "ai_taxonomy_001",
      label: "Taxonomy",
      canonical_path: ["AI", "Taxonomy"],
      version: "1.8.1",
      confidence: 0.98,
      document_count: 534,
      description: "Taxonomy management and organization"
    },
    {
      node_id: "ai_taxonomy_hierarchical_001",
      label: "Hierarchical",
      canonical_path: ["AI", "Taxonomy", "Hierarchical"],
      version: "1.8.1",
      confidence: 0.93,
      document_count: 298,
      description: "Hierarchical taxonomy structures"
    },
    {
      node_id: "ai_taxonomy_flat_001",
      label: "Flat",
      canonical_path: ["AI", "Taxonomy", "Flat"],
      version: "1.8.1",
      confidence: 0.88,
      document_count: 123,
      description: "Flat taxonomy structures"
    },
    {
      node_id: "ai_general_001",
      label: "General",
      canonical_path: ["AI", "General"],
      version: "1.8.1",
      confidence: 0.85,
      document_count: 678,
      description: "General AI concepts and applications"
    }
  ],
  edges: [
    { parent: "ai_root_001", child: "ai_ml_001", version: "1.8.1" },
    { parent: "ai_ml_001", child: "ai_ml_classification_001", version: "1.8.1" },
    { parent: "ai_ml_001", child: "ai_ml_clustering_001", version: "1.8.1" },
    { parent: "ai_root_001", child: "ai_rag_001", version: "1.8.1" },
    { parent: "ai_rag_001", child: "ai_rag_dynamic_001", version: "1.8.1" },
    { parent: "ai_rag_001", child: "ai_rag_static_001", version: "1.8.1" },
    { parent: "ai_root_001", child: "ai_taxonomy_001", version: "1.8.1" },
    { parent: "ai_taxonomy_001", child: "ai_taxonomy_hierarchical_001", version: "1.8.1" },
    { parent: "ai_taxonomy_001", child: "ai_taxonomy_flat_001", version: "1.8.1" },
    { parent: "ai_root_001", child: "ai_general_001", version: "1.8.1" }
  ],
  roots: ["ai_root_001"],
  last_updated: new Date().toISOString(),
  validation_status: {
    is_valid: true,
    errors: [],
    warnings: [],
    cycles: [],
    orphaned_nodes: []
  }
}

const mockVersions = ["latest", "1.8.1", "1.8.0", "1.7.9"]

export default function TaxonomyPage() {
  const { setTree, setVersions, setCurrentVersion, setLoading } = useTaxonomyStore()

  useEffect(() => {
    // Simulate loading data
    setLoading(true)

    setTimeout(() => {
      setTree(mockTaxonomyTree)
      setVersions(mockVersions)
      setCurrentVersion("1.8.1")
      setLoading(false)
    }, 1000)
  }, [setTree, setVersions, setCurrentVersion, setLoading])

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Taxonomy Management</h1>
            <p className="text-muted-foreground">
              Manage and explore your dynamic taxonomy structure with advanced search and filtering capabilities.
            </p>
          </div>
        </div>

        <TreePanel
          className="min-h-[600px]"
          showVersionDropdown={true}
          showMetrics={true}
          showFilters={true}
          maxHeight={800}
        />

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <div className="card-content p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Nodes</p>
                  <p className="text-2xl font-bold">{mockTaxonomyTree.total_nodes.toLocaleString()}</p>
                </div>
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 text-sm font-medium">{mockTaxonomyTree.total_nodes}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-content p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Documents</p>
                  <p className="text-2xl font-bold">{mockTaxonomyTree.total_documents.toLocaleString()}</p>
                </div>
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 text-sm font-medium">{mockTaxonomyTree.total_documents}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-content p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Current Version</p>
                  <p className="text-2xl font-bold">{mockTaxonomyTree.version}</p>
                </div>
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <span className="text-purple-600 text-sm font-medium">v</span>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-content p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Validation Status</p>
                  <p className="text-2xl font-bold text-green-600">Valid</p>
                </div>
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-green-600 text-sm font-medium">✓</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}