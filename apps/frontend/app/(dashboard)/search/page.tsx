"use client";

import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { search } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

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
      query,
      top_k: topK,
      use_hybrid: useHybrid,
    })
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Search</h1>
        <p className="text-muted-foreground">
          Search through your document knowledge base
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search Query</CardTitle>
          <CardDescription>Enter your search parameters</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="query">Query</Label>
              <Input
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your search query..."
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="topK">Top K Results</Label>
              <Input
                id="topK"
                type="number"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                min={1}
                max={100}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="useHybrid"
                checked={useHybrid}
                onCheckedChange={(checked) => setUseHybrid(checked === true)}
              />
              <Label htmlFor="useHybrid" className="cursor-pointer">
                Use Hybrid Search
              </Label>
            </div>

            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Searching..." : "Search"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {mutation.isError && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              {mutation.error instanceof Error ? mutation.error.message : "An error occurred"}
            </p>
          </CardContent>
        </Card>
      )}

      {mutation.isSuccess && mutation.data && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">
            Results ({mutation.data.total})
          </h2>
          {mutation.data.results.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <p className="text-center text-muted-foreground">
                  No results found
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {mutation.data.results.map((result) => (
                <Card key={result.chunk_id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-base">
                        Chunk ID: {result.chunk_id}
                      </CardTitle>
                      <span className="text-sm font-medium text-muted-foreground">
                        Score: {result.score.toFixed(4)}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <p className="text-sm">{result.content}</p>
                    {Object.keys(result.metadata).length > 0 && (
                      <div className="rounded-md bg-muted p-2">
                        <p className="text-xs font-medium mb-1">Metadata:</p>
                        <pre className="text-xs overflow-x-auto">
                          {JSON.stringify(result.metadata, null, 2)}
                        </pre>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
