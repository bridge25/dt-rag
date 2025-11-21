/**
 * Monitoring page for system health and performance
 *
 * @CODE:MONITORING-001
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api";
import { ModernCard } from "@/components/ui/modern-card";
import { IconBadge } from "@/components/ui/icon-badge";
import { Activity, Database, Server, CheckCircle2, XCircle, Clock } from "lucide-react";

export default function MonitoringPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30000,
  })

  return (
    <div className="space-y-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-6">
      <div>
        <h1 className="text-4xl font-bold tracking-tight">Monitoring</h1>
        <p className="mt-2 text-lg text-muted-foreground">
          System health and performance metrics
        </p>
      </div>

      {isLoading && (
        <ModernCard variant="beige">
          <div className="py-12">
            <p className="text-center text-gray-600">Loading health status...</p>
          </div>
        </ModernCard>
      )}

      {isError && (
        <ModernCard variant="purple">
          <div className="flex items-center gap-3">
            <IconBadge icon={XCircle} color="orange" />
            <div>
              <h3 className="text-xl font-semibold">System Error</h3>
              <p className="mt-1 text-sm text-white/70">
                Unable to fetch system health
              </p>
            </div>
          </div>
        </ModernCard>
      )}

      {data && (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <ModernCard variant="purple">
              <div className="flex items-center justify-between">
                <IconBadge icon={Activity} color="orange" size="lg" />
                {data.status === "healthy" ? (
                  <CheckCircle2 className="h-6 w-6 text-white/80" />
                ) : (
                  <XCircle className="h-6 w-6 text-red-400" />
                )}
              </div>
              <h4 className="mt-4 text-lg font-semibold">System Status</h4>
              <p className="mt-1 text-3xl font-bold capitalize">
                {data.status}
              </p>
              <p className="mt-2 text-sm text-white/70">Real-time monitoring</p>
            </ModernCard>

            <ModernCard variant="green">
              <div className="flex items-center justify-between">
                <IconBadge icon={Database} color="blue" size="lg" />
                {data.database === "healthy" ? (
                  <CheckCircle2 className="h-6 w-6 text-white/80" />
                ) : (
                  <XCircle className="h-6 w-6 text-red-400" />
                )}
              </div>
              <h4 className="mt-4 text-lg font-semibold">Database</h4>
              <p className="mt-1 text-3xl font-bold capitalize">
                {data.database}
              </p>
              <p className="mt-2 text-sm text-white/70">PostgreSQL + pgvector</p>
            </ModernCard>

            <ModernCard variant="dark">
              <div className="flex items-center justify-between">
                <IconBadge icon={Server} color="teal" size="lg" />
                {data.redis === "healthy" ? (
                  <CheckCircle2 className="h-6 w-6 text-white/80" />
                ) : (
                  <XCircle className="h-6 w-6 text-red-400" />
                )}
              </div>
              <h4 className="mt-4 text-lg font-semibold">Redis</h4>
              <p className="mt-1 text-3xl font-bold capitalize">
                {data.redis}
              </p>
              <p className="mt-2 text-sm text-white/70">Redis cache layer</p>
            </ModernCard>
          </div>

          <ModernCard variant="teal">
            <div className="flex items-center gap-3">
              <IconBadge icon={Clock} color="purple" />
              <div>
                <h4 className="text-lg font-semibold text-gray-900">Last Updated</h4>
                <p className="mt-1 text-xl font-medium text-gray-700">{data.timestamp}</p>
              </div>
            </div>
          </ModernCard>
        </>
      )}
    </div>
  );
}
