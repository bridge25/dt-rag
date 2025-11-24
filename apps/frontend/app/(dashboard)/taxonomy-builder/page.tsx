/**
 * Taxonomy Builder Page
 *
 * @CODE:TAXONOMY-BUILDER-001
 */

"use client"

import { TaxonomyBuilder } from "@/components/taxonomy-builder"

export default function TaxonomyBuilderPage() {
  return (
    <main className="p-6 max-w-7xl mx-auto">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Taxonomy Builder
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Create and manage your knowledge taxonomy structure
        </p>
      </header>

      <div className="h-[calc(100vh-200px)]">
        <TaxonomyBuilder taxonomyId="default" />
      </div>
    </main>
  )
}
