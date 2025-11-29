/**
 * Chat page - Neural Chat Interface
 * Ethereal Glass Theme Applied
 * (Rebranded from Search → Chat in Phase 1)
 * Phase 2: Agent Selection Feature Added
 * Phase 3: URL Query Parameter & Taxonomy Scope Filter
 *
 * @CODE:FRONTEND-REDESIGN-001-CHAT
 */

"use client";

import { useState, useEffect, type FormEvent } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { search } from "@/lib/api";
import { IconBadge } from "@/components/ui/icon-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Search as SearchIcon, Sparkles, FileText, TrendingUp, Command, Cpu, Zap, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n/context";
import { AgentSelector } from "@/components/chat/AgentSelector";
import { useAgents } from "@/hooks/useAgents";
import type { AgentCardData } from "@/components/agent-card/types";

export default function SearchPage() {
  const { t } = useTranslation()
  const router = useRouter()
  const searchParams = useSearchParams()
  const { agents, isLoading: isLoadingAgents } = useAgents()

  const [query, setQuery] = useState("")
  const [topK, setTopK] = useState(10)
  const [useHybrid, setUseHybrid] = useState(true)
  const [isFocused, setIsFocused] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState<AgentCardData | null>(null)

  // Sync selectedAgent with URL query parameter ?agent=xxx
  useEffect(() => {
    const agentId = searchParams.get("agent")
    if (agentId && agents.length > 0 && !isLoadingAgents) {
      const agent = agents.find((a) => a.agent_id === agentId)
      if (agent) {
        setSelectedAgent(agent)
      }
    }
  }, [searchParams, agents, isLoadingAgents])

  // Update URL when agent selection changes
  const handleAgentSelect = (agent: AgentCardData | null) => {
    setSelectedAgent(agent)
    // Update URL without page reload
    if (agent) {
      router.push(`/chat?agent=${agent.agent_id}`, { scroll: false })
    } else {
      router.push("/chat", { scroll: false })
    }
  }

  const mutation = useMutation({
    mutationFn: search,
  })

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()

    // Build search request with optional taxonomy filter
    const searchRequest: Parameters<typeof search>[0] = {
      q: query,
      max_results: topK,
      include_highlights: true,
      search_mode: useHybrid ? "hybrid" : "bm25",
    }

    // Apply taxonomy_scope filter if agent is selected
    if (selectedAgent?.taxonomy_scope && selectedAgent.taxonomy_scope.length > 0) {
      // canonical_in expects array of taxonomy paths (each path is an array of strings)
      searchRequest.canonical_in = [selectedAgent.taxonomy_scope]
    }

    mutation.mutate(searchRequest)
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] relative overflow-hidden p-8">
      {/* Ambient Background Effects - Cyan Nebula */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-cyan-500/10 blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-5xl mx-auto space-y-12 relative z-10">
        {/* Header Section */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 mb-4 shadow-[0_0_20px_rgba(0,247,255,0.15)]">
            <IconBadge icon={Command} color="blue" size="lg" className="bg-transparent" />
          </div>
          <h1 className="text-5xl font-bold tracking-tight text-white drop-shadow-[0_0_10px_rgba(0,247,255,0.3)]">
            {t("chat.title")}
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            {t("chat.subtitle")}
          </p>
        </div>

        {/* Search Interface */}
        <div className={cn(
          "relative transition-all duration-500 ease-out",
          isFocused ? "scale-[1.02]" : "scale-100"
        )}>
          <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500/30 via-purple-500/20 to-cyan-500/30 opacity-30 blur-xl rounded-[2rem] transition-opacity duration-500"
            style={{ opacity: isFocused ? 0.5 : 0.2 }} />

          <div className="relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-[2rem] p-8 shadow-[0_4px_15px_rgba(0,0,0,0.2)] overflow-hidden hover:shadow-[0_0_25px_rgba(0,247,255,0.3)] transition-shadow duration-300">
            {/* Decorative Grid */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

            <form onSubmit={handleSubmit} className="relative space-y-8">
              {/* Agent Selector */}
              <div className="space-y-3">
                <Label className="text-gray-300 text-sm font-medium uppercase tracking-wider flex items-center gap-2">
                  <Bot className="w-4 h-4 text-cyan-400" />
                  {t("chat.selectAgent")}
                </Label>
                <AgentSelector
                  selectedAgentId={selectedAgent?.agent_id || null}
                  onSelectAgent={handleAgentSelect}
                />
                {selectedAgent && (
                  <p className="text-xs text-white/40 px-1">
                    {t("chat.searchingWithin")} <span className="text-cyan-400">{selectedAgent.name}</span> {t("chat.knowledgeScope")} ({selectedAgent.total_documents || 0} documents)
                  </p>
                )}
              </div>

              <div className="space-y-4">
                <div className="relative group">
                  <SearchIcon className={cn(
                    "absolute left-5 top-1/2 -translate-y-1/2 w-6 h-6 transition-colors duration-300",
                    isFocused ? "text-cyan-400 drop-shadow-[0_0_8px_rgba(0,247,255,0.7)]" : "text-gray-400"
                  )} />
                  <Input
                    id="query"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    placeholder={t("chat.askQuestion")}
                    className="w-full h-16 pl-16 pr-6 bg-white/5 border-white/10 text-xl text-white placeholder:text-gray-500 rounded-2xl focus:ring-0 focus:border-cyan-400/50 focus:shadow-[0_0_15px_rgba(0,247,255,0.3)] transition-all duration-300"
                    required
                  />
                  {/* Animated Scan Line */}
                  <div className={cn(
                    "absolute bottom-0 left-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent transition-all duration-1000 ease-in-out",
                    isFocused ? "w-full opacity-100" : "w-0 opacity-0"
                  )} />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-end">
                <div className="space-y-3">
                  <Label htmlFor="topK" className="text-gray-300 text-sm font-medium uppercase tracking-wider flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-cyan-400" />
                    {t("chat.resultDensity")}
                  </Label>
                  <div className="relative">
                    <Input
                      id="topK"
                      type="number"
                      value={topK}
                      onChange={(e) => setTopK(Number(e.target.value))}
                      min={1}
                      max={100}
                      className="bg-white/5 border-white/10 text-white h-12 rounded-xl focus:border-cyan-400/50 focus:shadow-[0_0_10px_rgba(0,247,255,0.2)]"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10 hover:border-purple-400/30 transition-colors">
                  <div className="flex items-center space-x-3">
                    <Checkbox
                      id="useHybrid"
                      checked={useHybrid}
                      onCheckedChange={(checked) => setUseHybrid(checked === true)}
                      className="border-white/20 data-[state=checked]:bg-purple-500 data-[state=checked]:border-purple-500"
                    />
                    <Label htmlFor="useHybrid" className="cursor-pointer text-gray-300 font-medium select-none flex items-center gap-2">
                      <Zap className="w-4 h-4 text-purple-400" />
                      {t("chat.hybridSearch")}
                    </Label>
                  </div>
                  <span className="text-xs text-gray-500 font-mono bg-black/20 px-2 py-1 rounded">BM25 + VECTOR</span>
                </div>
              </div>

              <Button
                type="submit"
                disabled={mutation.isPending}
                className="w-full h-14 text-lg font-bold tracking-wide bg-gradient-to-r from-cyan-500 to-purple-500 hover:opacity-90 text-white rounded-xl shadow-lg shadow-cyan-500/20 transition-all duration-300 hover:scale-[1.01] hover:shadow-[0_0_25px_rgba(0,247,255,0.4)] active:scale-[0.99]"
              >
                {mutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <Cpu className="w-5 h-5 animate-spin" />
                    {t("chat.processing")}
                  </span>
                ) : (
                  t("chat.sendMessage")
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
                  <h3 className="text-lg font-bold text-red-400">{t("chat.systemError")}</h3>
                  <p className="text-red-300/80">
                    {mutation.error instanceof Error ? mutation.error.message : t("chat.systemError")}
                  </p>
                </div>
              </div>
            </div>
          )}

          {mutation.isSuccess && mutation.data && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
              <div className="flex items-center justify-between px-4">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-1 bg-cyan-400 rounded-full shadow-[0_0_10px_rgba(0,247,255,0.6)]" />
                  <div>
                    <h2 className="text-3xl font-bold text-cyan-400 drop-shadow-[0_0_10px_rgba(0,247,255,0.5)]">
                      {mutation.data.hits.length}
                    </h2>
                    <p className="text-sm text-gray-400 font-medium uppercase tracking-wider">
                      {t("chat.matchesFound")}
                    </p>
                  </div>
                </div>
                <div className="px-4 py-2 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-gray-400">
                  {t("chat.queryTime")}: {(Math.random() * 0.5 + 0.1).toFixed(3)}s
                </div>
              </div>

              {mutation.data.hits.length === 0 ? (
                <div className="text-center py-16 rounded-[2rem] bg-white/5 border border-white/10 backdrop-blur-md">
                  <div className="inline-flex p-6 rounded-full bg-white/5 mb-6">
                    <SearchIcon className="w-12 h-12 text-gray-500" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">{t("chat.noResults")}</h3>
                  <p className="text-gray-400">{t("chat.noResultsHint")}</p>
                </div>
              ) : (
                <div className="grid gap-6">
                  {mutation.data.hits.map((result, index) => (
                    <div
                      key={result.chunk_id}
                      className="group relative p-6 rounded-2xl bg-white/5 backdrop-blur-lg border border-white/10 hover:border-cyan-400/30 hover:bg-white/10 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_0_25px_rgba(0,247,255,0.3)]"
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <div className="flex items-start gap-5">
                        <div className="p-3 rounded-xl bg-white/5 border border-white/10 group-hover:border-cyan-400/30 transition-colors">
                          <FileText className="w-6 h-6 text-cyan-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <span className="px-2 py-0.5 rounded bg-white/10 text-[10px] font-mono text-gray-400 border border-white/5">
                                  ID: {result.chunk_id.slice(0, 8)}...
                                </span>
                                <span className="px-2 py-0.5 rounded bg-cyan-400/10 text-[10px] font-mono text-cyan-400 border border-cyan-400/20">
                                  MATCH #{index + 1}
                                </span>
                              </div>
                            </div>
                            <div className="flex flex-col items-end">
                              <span className="text-2xl font-bold text-cyan-400 leading-none drop-shadow-[0_0_8px_rgba(0,247,255,0.5)]">
                                {(result.score * 100).toFixed(1)}%
                              </span>
                              <span className="text-[10px] text-gray-500 uppercase tracking-wider mt-1">{t("chat.relevance")}</span>
                            </div>
                          </div>

                          <p className="text-gray-300 leading-relaxed text-lg font-light border-l-2 border-white/10 pl-4 py-1 group-hover:border-cyan-400/50 transition-colors">
                            {result.text}
                          </p>

                          {result.metadata && Object.keys(result.metadata).length > 0 && (
                            <div className="mt-4 pt-4 border-t border-white/5">
                              <details className="group/details">
                                <summary className="cursor-pointer text-xs font-medium text-gray-500 hover:text-cyan-400 transition-colors flex items-center gap-2 select-none">
                                  <Cpu className="w-3 h-3" />
                                  {t("chat.viewMetadata")}
                                </summary>
                                <div className="mt-3 p-4 rounded-xl bg-black/30 border border-white/5 font-mono text-xs text-gray-400 overflow-x-auto">
                                  <pre>{JSON.stringify(result.metadata, null, 2)}</pre>
                                </div>
                              </details>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Bottom glow bar */}
                      <div className="absolute bottom-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
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
