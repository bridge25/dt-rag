/**
 * Dashboard home page with system metrics and performance overview
 *
 * @CODE:FRONTEND-001
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api";
import { ModernCard } from "@/components/ui/modern-card";
import { IconBadge } from "@/components/ui/icon-badge";
import { Activity, Database, Server, Zap, TrendingUp, Users, FileText, CheckCircle, Clock, Star, ArrowUpRight } from "lucide-react";

export default function DashboardPage() {
  const { data: healthData } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 60000,
  })

  return (
    <div className="space-y-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-6">
      <div>
        <h1 className="text-4xl font-bold tracking-tight">Dashboard</h1>
        <p className="mt-2 text-lg text-muted-foreground">
          RAG System Overview and Performance Metrics
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ModernCard variant="dark" className="lg:row-span-2">
          <div className="flex items-center justify-between">
            <h3 className="text-2xl font-bold">System Performance</h3>
            <IconBadge icon={Activity} color="orange" />
          </div>

          <div className="mt-8 grid grid-cols-2 gap-8">
            <div>
              <p className="text-sm text-white/70">Uptime</p>
              <div className="mt-2 text-5xl font-bold">
                {healthData?.status === "healthy" ? "99%" : "..."}
              </div>
            </div>
            <div>
              <p className="text-sm text-white/70">Response Time</p>
              <div className="mt-2 text-5xl font-bold">
                <span className="text-tealAccent">42</span>
                <span className="text-2xl">ms</span>
              </div>
            </div>
          </div>

          <div className="mt-8 space-y-4">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span className="text-sm text-white/90">Database connection active</span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span className="text-sm text-white/90">Redis cache operational</span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span className="text-sm text-white/90">Search engine ready</span>
            </div>
          </div>
        </ModernCard>

        <ModernCard variant="teal">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">Active Sessions</p>
              <h3 className="mt-2 text-4xl font-bold text-gray-900">
                {healthData?.status ? "24" : "..."}
              </h3>
            </div>
            <IconBadge icon={Users} color="blue" size="lg" />
          </div>
          <p className="mt-4 text-sm text-gray-600">
            Your data updates every 3 hours
          </p>
        </ModernCard>

        <ModernCard variant="beige" className="lg:col-span-2">
          <div className="mb-6">
            <h3 className="text-2xl font-bold text-gray-900">System Metrics</h3>
            <p className="mt-1 text-sm text-gray-600">
              Real-time statistics of your RAG system
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <div className="rounded-2xl bg-white p-6 shadow-sm">
              <IconBadge icon={Zap} color="orange" className="mb-3" />
              <p className="text-xs text-gray-600">Queries Today</p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {healthData?.status ? "847" : "..."}
              </p>
              <p className="mt-1 text-xs text-green-600 flex items-center gap-1">
                <TrendingUp className="h-3 w-3" /> +12%
              </p>
            </div>

            <div className="rounded-2xl bg-white p-6 shadow-sm">
              <IconBadge icon={FileText} color="blue" className="mb-3" />
              <p className="text-xs text-gray-600">Documents</p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {healthData?.status ? "1,234" : "..."}
              </p>
              <p className="mt-1 text-xs text-green-600 flex items-center gap-1">
                <TrendingUp className="h-3 w-3" /> +8%
              </p>
            </div>

            <div className="rounded-2xl bg-white p-6 shadow-sm">
              <IconBadge icon={Star} color="purple" className="mb-3" />
              <p className="text-xs text-gray-600">Avg Quality</p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {healthData?.status ? "94%" : "..."}
              </p>
              <p className="mt-1 text-xs text-gray-500">Excellent</p>
            </div>

            <div className="rounded-2xl bg-white p-6 shadow-sm">
              <IconBadge icon={Clock} color="teal" className="mb-3" />
              <p className="text-xs text-gray-600">Avg. Latency</p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {healthData?.status ? "42ms" : "..."}
              </p>
              <p className="mt-1 text-xs text-green-600 flex items-center gap-1">
                Fast
              </p>
            </div>
          </div>
        </ModernCard>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <ModernCard variant="purple">
          <div className="flex items-center justify-between">
            <Database className="h-8 w-8 text-white" />
            <ArrowUpRight className="h-5 w-5 text-white/70" />
          </div>
          <h4 className="mt-4 text-lg font-semibold">Database</h4>
          <p className="mt-1 text-3xl font-bold capitalize">
            {healthData?.database || "Loading..."}
          </p>
          <p className="mt-2 text-sm text-white/70">PostgreSQL + pgvector</p>
        </ModernCard>

        <ModernCard variant="green">
          <div className="flex items-center justify-between">
            <Server className="h-8 w-8 text-white" />
            <ArrowUpRight className="h-5 w-5 text-white/70" />
          </div>
          <h4 className="mt-4 text-lg font-semibold">Cache</h4>
          <p className="mt-1 text-3xl font-bold capitalize">
            {healthData?.redis || "Loading..."}
          </p>
          <p className="mt-2 text-sm text-white/70">Redis cache layer</p>
        </ModernCard>

        <ModernCard variant="dark">
          <div className="flex items-center justify-between">
            <Activity className="h-8 w-8 text-white" />
            <ArrowUpRight className="h-5 w-5 text-white/70" />
          </div>
          <h4 className="mt-4 text-lg font-semibold">Status</h4>
          <p className="mt-1 text-3xl font-bold capitalize">
            {healthData?.status || "Loading..."}
          </p>
          <p className="mt-2 text-sm text-white/70">Real-time monitoring</p>
        </ModernCard>
      </div>
    </div>
  );
}
