"use client";

import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { search } from "@/lib/api";
import { ModernCard } from "@/components/ui/modern-card";
import { IconBadge } from "@/components/ui/icon-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Search as SearchIcon, Sparkles, FileText, TrendingUp } from "lucide-react";

export default function SearchPage() {
  const [query, setQuery] = useState("")
  const [topK, setTopK] = useState(10)
  const [useHybrid, setUseHybrid] = useState(true)

  const mutation = useMutation({
    mutationFn: search,
  })

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    mutation.mutate({
      q: query,
      max_results: topK,
      include_highlights: true,
      search_mode: useHybrid ? "hybrid" : "bm25",
    })
  }

  return (
    <div className="space-y-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-6">
      <div>
        <h1 className="text-4xl font-bold tracking-tight">Search</h1>
        <p className="mt-2 text-lg text-muted-foreground">
          Intelligent hybrid search through your knowledge base
        </p>
      </div>

      <ModernCard variant="dark">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-bold">Search Query</h3>
          <IconBadge icon={SearchIcon} color="blue" size="lg" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-3">
            <Label htmlFor="query" className="text-white/90 text-base">Query</Label>
            <Input
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What would you like to search for?"
              className="bg-white/10 border-white/20 text-white placeholder:text-white/50 h-12 text-base"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-3">
              <Label htmlFor="topK" className="text-white/90 text-base">Top K Results</Label>
              <Input
                id="topK"
                type="number"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                min={1}
                max={100}
                className="bg-white/10 border-white/20 text-white h-12"
              />
            </div>

            <div className="flex items-end">
              <div className="flex items-center space-x-3 pb-3">
                <Checkbox
                  id="useHybrid"
                  checked={useHybrid}
                  onCheckedChange={(checked) => setUseHybrid(checked === true)}
                  className="border-white/20"
                />
                <Label htmlFor="useHybrid" className="cursor-pointer text-white/90 text-base">
                  Use Hybrid Search (BM25 + Vector)
                </Label>
              </div>
            </div>
          </div>

          <Button
            type="submit"
            disabled={mutation.isPending}
            className="w-full h-12 text-base bg-tealAccent hover:bg-tealAccent/90 text-gray-900"
          >
            {mutation.isPending ? "Searching..." : "Search"}
          </Button>
        </form>
      </ModernCard>

      {mutation.isError && (
        <ModernCard variant="default" className="border-red-500 border-2">
          <div className="flex items-center gap-3">
            <IconBadge icon={Sparkles} color="red" />
            <div>
              <h3 className="text-lg font-bold text-red-600">Search Error</h3>
              <p className="text-sm text-muted-foreground mt-1">
                {mutation.error instanceof Error ? mutation.error.message : "An error occurred"}
              </p>
            </div>
          </div>
        </ModernCard>
      )}

      {mutation.isSuccess && mutation.data && (
        <div className="space-y-6">
          <ModernCard variant="teal">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-bold text-gray-900">
                  {mutation.data.hits.length}
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  Results found
                </p>
              </div>
              <IconBadge icon={TrendingUp} color="green" size="lg" />
            </div>
          </ModernCard>

          {mutation.data.hits.length === 0 ? (
            <ModernCard variant="beige">
              <div className="text-center py-8">
                <IconBadge icon={SearchIcon} color="orange" size="lg" className="mx-auto mb-4" />
                <p className="text-lg font-medium text-gray-700">
                  No results found
                </p>
                <p className="text-sm text-gray-600 mt-2">
                  Try adjusting your search query
                </p>
              </div>
            </ModernCard>
          ) : (
            <div className="grid gap-4">
              {mutation.data.hits.map((result, index) => (
                <ModernCard key={result.chunk_id} variant="default">
                  <div className="flex items-start gap-4">
                    <IconBadge icon={FileText} color="blue" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">
                            Result #{index + 1}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Chunk ID: {result.chunk_id}
                          </p>
                        </div>
                        <div className="rounded-full bg-orangePrimary/20 px-3 py-1">
                          <span className="text-sm font-bold text-orangePrimary">
                            {result.score.toFixed(4)}
                          </span>
                        </div>
                      </div>

                      <p className="text-base leading-relaxed text-gray-800 dark:text-gray-200">
                        {result.text}
                      </p>

                      {result.metadata && Object.keys(result.metadata).length > 0 && (
                        <div className="mt-4 rounded-xl bg-gray-100 dark:bg-gray-800 p-4">
                          <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">
                            Metadata:
                          </p>
                          <pre className="text-xs overflow-x-auto text-gray-700 dark:text-gray-300">
                            {JSON.stringify(result.metadata, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                </ModernCard>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
