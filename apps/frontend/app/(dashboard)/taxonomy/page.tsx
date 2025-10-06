"use client";

import { useQuery } from "@tanstack/react-query";
import { getTaxonomyTree } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Network } from "lucide-react";

export default function TaxonomyPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["taxonomy"],
    queryFn: () => getTaxonomyTree("1.8.1"),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Taxonomy</h1>
        <p className="text-muted-foreground">
          Browse and manage your classification taxonomy
        </p>
      </div>

      {isLoading && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">Loading taxonomy...</p>
          </CardContent>
        </Card>
      )}

      {isError && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Failed to load taxonomy tree
            </p>
          </CardContent>
        </Card>
      )}

      {data && (
        <div className="grid gap-4">
          {data.map((node) => (
            <Card key={node.id}>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Network className="h-5 w-5" />
                  <CardTitle>{node.name}</CardTitle>
                </div>
                <CardDescription>
                  Level {node.level} - Path: {node.path.join(" > ")}
                </CardDescription>
              </CardHeader>
              {node.children && node.children.length > 0 && (
                <CardContent>
                  <div className="space-y-2 pl-6 border-l-2">
                    {node.children.map((child) => (
                      <div key={child.id} className="text-sm">
                        <p className="font-medium">{child.name}</p>
                        <p className="text-muted-foreground">
                          Level {child.level}
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
