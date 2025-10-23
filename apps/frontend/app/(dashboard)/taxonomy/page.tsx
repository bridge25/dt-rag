"use client";

import { useQuery } from "@tanstack/react-query";
import { getTaxonomyTree } from "@/lib/api";
import { ModernCard } from "@/components/ui/modern-card";
import { IconBadge } from "@/components/ui/icon-badge";
import { Network, ChevronRight, FolderTree } from "lucide-react";

export default function TaxonomyPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["taxonomy"],
    queryFn: () => getTaxonomyTree("1.8.1"),
  })

  const getVariant = (index: number) => {
    const variants = ["purple", "green", "teal"] as const;
    return variants[index % variants.length];
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-teal-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="space-y-6 p-8">
        <div className="flex items-center gap-4">
          <IconBadge icon={FolderTree} color="purple" size="lg" />
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Taxonomy</h1>
            <p className="text-muted-foreground">
              Browse and manage your classification taxonomy
            </p>
          </div>
        </div>

        {isLoading && (
          <ModernCard>
            <p className="text-center text-muted-foreground py-8">Loading taxonomy...</p>
          </ModernCard>
        )}

        {isError && (
          <ModernCard variant="default" className="border-2 border-destructive">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <IconBadge icon={Network} color="red" size="sm" />
                <h3 className="text-lg font-semibold text-destructive">Error</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Failed to load taxonomy tree
              </p>
            </div>
          </ModernCard>
        )}

        {data && (
          <div className="grid gap-6">
            {data.map((node, index) => (
              <ModernCard key={node.id} variant={getVariant(index)}>
                <div className="space-y-4">
                  <div className="flex items-start gap-4">
                    <IconBadge
                      icon={Network}
                      color={getVariant(index) === "purple" ? "purple" : getVariant(index) === "green" ? "green" : "teal"}
                      size="md"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h2 className="text-2xl font-bold truncate">{node.name}</h2>
                        <IconBadge
                          icon={ChevronRight}
                          color="orange"
                          size="sm"
                          className="opacity-60"
                        />
                      </div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="inline-flex items-center px-3 py-1 rounded-full bg-white/20 backdrop-blur-sm text-sm font-medium">
                          Level {node.level}
                        </span>
                        <span className="text-sm opacity-80">
                          Path: {node.path.join(" > ")}
                        </span>
                      </div>
                    </div>
                  </div>

                  {node.children && node.children.length > 0 && (
                    <div className="mt-6 pl-4 border-l-4 border-white/30 space-y-4">
                      {node.children.map((child) => (
                        <div
                          key={child.id}
                          className="group transition-all duration-200 hover:translate-x-2"
                        >
                          <div className="flex items-center gap-3 p-4 rounded-xl bg-white/10 backdrop-blur-sm hover:bg-white/20 transition-colors">
                            <ChevronRight className="h-5 w-5 opacity-60 group-hover:opacity-100 transition-opacity" />
                            <div className="flex-1 min-w-0">
                              <p className="text-lg font-semibold truncate">{child.name}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-white/20 text-xs font-medium">
                                  Level {child.level}
                                </span>
                                {child.children && child.children.length > 0 && (
                                  <span className="text-xs opacity-60">
                                    {child.children.length} child{child.children.length !== 1 ? "ren" : ""}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>

                          {child.children && child.children.length > 0 && (
                            <div className="mt-2 ml-8 pl-4 border-l-2 border-white/20 space-y-2">
                              {child.children.map((grandchild) => (
                                <div
                                  key={grandchild.id}
                                  className="flex items-center gap-2 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                                >
                                  <ChevronRight className="h-4 w-4 opacity-40" />
                                  <div className="flex-1 min-w-0">
                                    <p className="text-base font-medium truncate">{grandchild.name}</p>
                                    <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-white/15 text-xs mt-1">
                                      Level {grandchild.level}
                                    </span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </ModernCard>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
