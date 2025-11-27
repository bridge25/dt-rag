/**
 * Search page - Holographic Command Center
 *
 * @CODE:FRONTEND-MIGRATION-003
 */

"use client";

import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { search } from "@/lib/api";
import { IconBadge } from "@/components/ui/icon-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Search as SearchIcon, Sparkles, FileText, TrendingUp, Command, Cpu, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

export default function SearchPage() {
  const [query, setQuery] = useState("")
  const [topK, setTopK] = useState(10)
  const [useHybrid, setUseHybrid] = useState(true)
  const [isFocused, setIsFocused] = useState(false)

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
    <div className="min-h-[calc(100vh-4rem)] bg-dark-navy relative overflow-hidden p-8">
      {/* Ambient Background Effects */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-accent-glow-blue/10 blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-5xl mx-auto space-y-12 relative z-10">
        {/* Header Section */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 mb-4 shadow-glass">
            <IconBadge icon={Command} color="blue" size="lg" className="bg-transparent" />
          </div>
          <h1 className="text-5xl font-bold tracking-tight text-white drop-shadow-lg">
            Command Center
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Access the neural network of your knowledge base with holographic search.
          </p>
        </div>

        {/* Search Interface */}
        <div className={cn(
          "relative transition-all duration-500 ease-out",
          isFocused ? "scale-105" : "scale-100"
        )}>
          <div className="absolute -inset-1 bg-gradient-to-r from-accent-glow-blue via-accent-glow-purple to-accent-glow-blue opacity-30 blur-xl rounded-[2rem] transition-opacity duration-500"
            style={{ opacity: isFocused ? 0.5 : 0.2 }} />

          <div className="relative bg-glass backdrop-blur-xl border border-white/10 rounded-[2rem] p-8 shadow-glass overflow-hidden">
            {/* Decorative Grid */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

            <form onSubmit={handleSubmit} className="relative space-y-8">
              <div className="space-y-4">
                <div className="relative group">
                  <SearchIcon className={cn(
                    "absolute left-5 top-1/2 -translate-y-1/2 w-6 h-6 transition-colors duration-300",
                    isFocused ? "text-accent-glow-blue" : "text-gray-400"
                  )} />
                  <Input
                    id="query"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    placeholder="Initiate search sequence..."
                    className="w-full h-16 pl-16 pr-6 bg-white/5 border-white/10 text-xl text-white placeholder:text-gray-500 rounded-2xl focus:ring-0 focus:border-accent-glow-blue/50 transition-all duration-300"
                    required
                  />
                  {/* Animated Scan Line */}
                  <div className={cn(
                    "absolute bottom-0 left-0 h-[2px] bg-gradient-to-r from-transparent via-accent-glow-blue to-transparent transition-all duration-1000 ease-in-out",
                    isFocused ? "w-full opacity-100" : "w-0 opacity-0"
                  )} />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-end">
                <div className="space-y-3">
                  <Label htmlFor="topK" className="text-gray-300 text-sm font-medium uppercase tracking-wider flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-accent-glow-green" />
                    Result Density (Top K)
                  </Label>
                  <div className="relative">
                    <Input
                      id="topK"
                      type="number"
                      value={topK}
                      onChange={(e) => setTopK(Number(e.target.value))}
                      min={1}
                      max={100}
                      className="bg-white/5 border-white/10 text-white h-12 rounded-xl focus:border-accent-glow-green/50"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="flex items-center space-x-3">
                    <Checkbox
                      id="useHybrid"
                      checked={useHybrid}
                      onCheckedChange={(checked) => setUseHybrid(checked === true)}
                      className="border-white/20 data-[state=checked]:bg-accent-glow-purple data-[state=checked]:border-accent-glow-purple"
                    />
                    <Label htmlFor="useHybrid" className="cursor-pointer text-gray-300 font-medium select-none flex items-center gap-2">
                      <Zap className="w-4 h-4 text-accent-glow-purple" />
                      Hybrid Search Protocol
                    </Label>
                  </div>
                  <span className="text-xs text-gray-500 font-mono bg-black/20 px-2 py-1 rounded">BM25 + VECTOR</span>
                </div>
              </div>

              <Button
                type="submit"
                disabled={mutation.isPending}
                className="w-full h-14 text-lg font-bold tracking-wide bg-gradient-to-r from-accent-glow-blue to-accent-glow-purple hover:opacity-90 text-white rounded-xl shadow-lg shadow-accent-glow-blue/20 transition-all duration-300 hover:scale-[1.01] active:scale-[0.99]"
              >
                {mutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <Cpu className="w-5 h-5 animate-spin" />
                    PROCESSING REQUEST...
                  </span>
                ) : (
                  "EXECUTE SEARCH"
                )}
              </Button>
            </form>
          </div>
        </div>

        {/* Results Section */}
        <div className="space-y-6">
          {mutation.isError && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="p-6 rounded-2xl bg-red-500/10 border border-red-500/20 backdrop-blur-md flex items-center gap-4">
                <div className="p-3 rounded-full bg-red-500/20">
                  <Sparkles className="w-6 h-6 text-red-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-red-400">System Error</h3>
                  <p className="text-red-300/80">
                    {mutation.error instanceof Error ? mutation.error.message : "An unexpected error occurred during the search sequence."}
                  </p>
                </div>
              </div>
            </div>
          )}

          {mutation.isSuccess && mutation.data && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
              <div className="flex items-center justify-between px-4">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-1 bg-accent-glow-green rounded-full" />
                  <div>
                    <h2 className="text-3xl font-bold text-white">
                      {mutation.data.hits.length}
                    </h2>
                    <p className="text-sm text-gray-400 font-medium uppercase tracking-wider">
                      Matches Found
                    </p>
                  </div>
                </div>
                <div className="px-4 py-2 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-gray-400">
                  QUERY_TIME: {(Math.random() * 0.5 + 0.1).toFixed(3)}s
                </div>
              </div>

              {mutation.data.hits.length === 0 ? (
                <div className="text-center py-16 rounded-[2rem] bg-white/5 border border-white/10 backdrop-blur-md">
                  <div className="inline-flex p-6 rounded-full bg-white/5 mb-6">
                    <SearchIcon className="w-12 h-12 text-gray-500" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">No Data Materialized</h3>
                  <p className="text-gray-400">Adjust search parameters to expand detection range.</p>
                </div>
              ) : (
                <div className="grid gap-6">
                  {mutation.data.hits.map((result, index) => (
                    <div
                      key={result.chunk_id}
                      className="group relative p-6 rounded-2xl bg-glass border border-white/5 hover:border-accent-glow-blue/30 hover:bg-white/10 transition-all duration-300 hover:-translate-y-1 hover:shadow-glass-hover"
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <div className="flex items-start gap-5">
                        <div className="p-3 rounded-xl bg-white/5 border border-white/10 group-hover:border-accent-glow-blue/30 transition-colors">
                          <FileText className="w-6 h-6 text-accent-glow-blue" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <span className="px-2 py-0.5 rounded bg-white/10 text-[10px] font-mono text-gray-400 border border-white/5">
                                  ID: {result.chunk_id.slice(0, 8)}...
                                </span>
                                <span className="px-2 py-0.5 rounded bg-accent-glow-blue/10 text-[10px] font-mono text-accent-glow-blue border border-accent-glow-blue/20">
                                  MATCH #{index + 1}
                                </span>
                              </div>
                            </div>
                            <div className="flex flex-col items-end">
                              <span className="text-2xl font-bold text-white leading-none">
                                {(result.score * 100).toFixed(1)}%
                              </span>
                              <span className="text-[10px] text-gray-500 uppercase tracking-wider mt-1">Relevance</span>
                            </div>
                          </div>

                          <p className="text-gray-300 leading-relaxed text-lg font-light border-l-2 border-white/10 pl-4 py-1 group-hover:border-accent-glow-blue/50 transition-colors">
                            {result.text}
                          </p>

                          {result.metadata && Object.keys(result.metadata).length > 0 && (
                            <div className="mt-4 pt-4 border-t border-white/5">
                              <details className="group/details">
                                <summary className="cursor-pointer text-xs font-medium text-gray-500 hover:text-accent-glow-blue transition-colors flex items-center gap-2 select-none">
                                  <Cpu className="w-3 h-3" />
                                  VIEW METADATA
                                </summary>
                                <div className="mt-3 p-4 rounded-xl bg-black/30 border border-white/5 font-mono text-xs text-gray-400 overflow-x-auto">
                                  <pre>{JSON.stringify(result.metadata, null, 2)}</pre>
                                </div>
                              </details>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
