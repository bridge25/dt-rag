"use client";

import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Database, Server } from "lucide-react";

export default function DashboardPage() {
  const { data: healthData } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 60000,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          RAG System Overview and Statistics
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">
              {healthData?.status || "Loading..."}
            </div>
            <p className="text-xs text-muted-foreground">
              Real-time monitoring
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Database</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">
              {healthData?.database || "Loading..."}
            </div>
            <p className="text-xs text-muted-foreground">
              PostgreSQL + pgvector
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cache</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">
              {healthData?.redis || "Loading..."}
            </div>
            <p className="text-xs text-muted-foreground">
              Redis cache layer
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Get started with common tasks
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <a
            href="/search"
            className="block rounded-lg border p-4 hover:bg-accent transition-colors"
          >
            <h3 className="font-semibold">Search Documents</h3>
            <p className="text-sm text-muted-foreground">
              Find relevant information using hybrid search
            </p>
          </a>
          <a
            href="/documents"
            className="block rounded-lg border p-4 hover:bg-accent transition-colors"
          >
            <h3 className="font-semibold">Upload Documents</h3>
            <p className="text-sm text-muted-foreground">
              Add new documents to your knowledge base
            </p>
          </a>
        </CardContent>
      </Card>
    </div>
  );
}
