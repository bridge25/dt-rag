/**
 * Monitoring page for system health and performance
 * Ethereal Glass Aesthetic
 *
 * @CODE:MONITORING-002
 */

"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api";
import {
  Activity,
  Database,
  Server,
  CheckCircle2,
  XCircle,
  Clock,
  Terminal,
  Cpu,
} from "lucide-react";

export default function MonitoringPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30000,
  });

  const [logs, setLogs] = useState<string[]>([]);

  // Simulate log stream
  useEffect(() => {
    const interval = setInterval(() => {
      const newLog = `[${new Date().toLocaleTimeString()}] INFO: System check completed. Latency: ${Math.floor(Math.random() * 50) + 10}ms`;
      setLogs(prev => [newLog, ...prev].slice(0, 50));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8 p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">System Monitoring</h1>
          <p className="mt-1 text-white/60">Real-time health & performance metrics</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-sm font-medium animate-pulse">
          <div className="h-2 w-2 rounded-full bg-green-500" />
          Live System
        </div>
      </div>

      {/* Health Grid */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* System Status */}
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md group hover:bg-white/10 transition-all duration-300">
          <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-purple-500/20 blur-2xl group-hover:bg-purple-500/30 transition-all" />

          <div className="flex items-center justify-between relative z-10 mb-4">
            <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Activity className="w-6 h-6" />
            </div>
            {data?.status === "healthy" ? (
              <CheckCircle2 className="h-6 w-6 text-green-400" />
            ) : (
              <XCircle className="h-6 w-6 text-red-400" />
            )}
          </div>

          <h3 className="text-lg font-semibold text-white">System Status</h3>
          <p className="text-3xl font-bold text-white mt-1 capitalize">
            {isLoading ? "Checking..." : data?.status || "Unknown"}
          </p>
          <p className="text-sm text-white/40 mt-2">Core services operational</p>
        </div>

        {/* Database Status */}
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md group hover:bg-white/10 transition-all duration-300">
          <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-blue-500/20 blur-2xl group-hover:bg-blue-500/30 transition-all" />

          <div className="flex items-center justify-between relative z-10 mb-4">
            <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <Database className="w-6 h-6" />
            </div>
            {data?.database === "healthy" ? (
              <CheckCircle2 className="h-6 w-6 text-green-400" />
            ) : (
              <XCircle className="h-6 w-6 text-red-400" />
            )}
          </div>

          <h3 className="text-lg font-semibold text-white">Database</h3>
          <p className="text-3xl font-bold text-white mt-1 capitalize">
            {isLoading ? "Checking..." : data?.database || "Unknown"}
          </p>
          <p className="text-sm text-white/40 mt-2">PostgreSQL + pgvector</p>
        </div>

        {/* Redis Status */}
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md group hover:bg-white/10 transition-all duration-300">
          <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-orange-500/20 blur-2xl group-hover:bg-orange-500/30 transition-all" />

          <div className="flex items-center justify-between relative z-10 mb-4">
            <div className="p-3 rounded-xl bg-orange-500/10 border border-orange-500/20 text-orange-400">
              <Server className="w-6 h-6" />
            </div>
            {data?.redis === "healthy" ? (
              <CheckCircle2 className="h-6 w-6 text-green-400" />
            ) : (
              <XCircle className="h-6 w-6 text-red-400" />
            )}
          </div>

          <h3 className="text-lg font-semibold text-white">Redis Cache</h3>
          <p className="text-3xl font-bold text-white mt-1 capitalize">
            {isLoading ? "Checking..." : data?.redis || "Unknown"}
          </p>
          <p className="text-sm text-white/40 mt-2">In-memory data store</p>
        </div>
      </div>

      {/* System Metrics & Logs */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Metrics Panel */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
          <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-blue-400" />
            Resource Usage
          </h3>

          <div className="space-y-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-white/60">CPU Load</span>
                <span className="text-white font-mono">42%</span>
              </div>
              <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                <div className="h-full w-[42%] bg-blue-500 rounded-full" />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-white/60">Memory Usage</span>
                <span className="text-white font-mono">2.4GB / 8GB</span>
              </div>
              <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                <div className="h-full w-[30%] bg-purple-500 rounded-full" />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-white/60">Disk I/O</span>
                <span className="text-white font-mono">125 MB/s</span>
              </div>
              <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                <div className="h-full w-[65%] bg-orange-500 rounded-full" />
              </div>
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-white/10">
            <div className="flex items-center gap-3 text-sm text-white/60">
              <Clock className="w-4 h-4" />
              Last Updated: {data?.timestamp ? new Date(data.timestamp).toLocaleTimeString() : "Syncing..."}
            </div>
          </div>
        </div>

        {/* Live Logs Terminal */}
        <div className="lg:col-span-2 rounded-2xl border border-white/10 bg-black/40 p-6 backdrop-blur-md flex flex-col h-[400px]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Terminal className="w-5 h-5 text-green-400" />
              System Logs
            </h3>
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
              <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto font-mono text-sm space-y-2 custom-scrollbar pr-2">
            {logs.map((log, i) => (
              <div key={i} className="text-green-400/80 border-l-2 border-green-500/20 pl-3">
                <span className="opacity-50 mr-2">$</span>
                {log}
              </div>
            ))}
            <div className="animate-pulse text-green-400">_</div>
          </div>
        </div>
      </div>
    </div>
  );
}
