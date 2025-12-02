/**
 * Connect page - External Integration Hub
 * Ethereal Glass Theme Applied
 *
 * Manage API Keys, MCP Servers, and Communication Channels
 *
 * @CODE:FRONTEND-REDESIGN-001-CONNECT
 */

"use client";

import { useState } from "react";
import {
  Plug,
  Key,
  Server,
  MessageCircle,
  Sparkles,
  Plus,
  Copy,
  Trash2,
  CheckCircle2,
  ExternalLink,
  Settings,
  Globe,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

// Mock data for demo
const MOCK_API_KEYS = [
  {
    id: "key-1",
    name: "Production API Key",
    prefix: "dt_prod_",
    created_at: "2024-11-20",
    last_used: "2024-11-28",
    status: "active",
  },
  {
    id: "key-2",
    name: "Development Key",
    prefix: "dt_dev_",
    created_at: "2024-11-15",
    last_used: "2024-11-27",
    status: "active",
  },
];

const MOCK_MCP_SERVERS = [
  {
    id: "mcp-1",
    name: "Context7 Documentation",
    url: "mcp://context7.ai",
    status: "connected",
    tools_count: 2,
  },
  {
    id: "mcp-2",
    name: "Playwright Browser",
    url: "mcp://playwright.local",
    status: "connected",
    tools_count: 18,
  },
  {
    id: "mcp-3",
    name: "Notion Integration",
    url: "mcp://notion.ai",
    status: "disconnected",
    tools_count: 12,
  },
];

const MOCK_CHANNELS = [
  {
    id: "ch-1",
    name: "Web Widget",
    type: "widget",
    status: "active",
    icon: Globe,
  },
  {
    id: "ch-2",
    name: "Slack Integration",
    type: "slack",
    status: "pending",
    icon: MessageCircle,
  },
  {
    id: "ch-3",
    name: "REST API",
    type: "api",
    status: "active",
    icon: Settings,
  },
];

export default function ConnectPage() {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleCopyKey = (keyId: string) => {
    // In real implementation, would copy the actual key
    navigator.clipboard.writeText(`dt_xxxxxx_${keyId}`);
    setCopiedKey(keyId);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] relative overflow-hidden p-8">
      {/* Ambient Background Effects - Purple/Cyan Nebula */}
      <div className="absolute top-20 right-20 w-[600px] h-[600px] bg-purple-500/10 blur-[150px] rounded-full pointer-events-none" />
      <div className="absolute bottom-20 left-20 w-[400px] h-[400px] bg-cyan-500/10 blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        {/* Header Section */}
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 shadow-[0_0_20px_rgba(139,92,246,0.15)]">
            <Plug className="h-8 w-8 text-purple-400 drop-shadow-[0_0_8px_rgba(139,92,246,0.7)]" />
          </div>
          <div>
            <h1 className="text-4xl font-bold tracking-tight text-white flex items-center gap-3">
              <Sparkles className="w-6 h-6 text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.7)]" />
              Connect Hub
            </h1>
            <p className="text-gray-400 mt-1">
              Manage external integrations and communication channels
            </p>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {/* API Keys Section */}
          <div className="xl:col-span-1 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Key className="w-5 h-5 text-cyan-400" />
                <h2 className="text-lg font-semibold text-white">API Keys</h2>
              </div>
              <Button
                size="sm"
                className="bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 border border-cyan-500/30"
              >
                <Plus className="w-4 h-4 mr-1" />
                New Key
              </Button>
            </div>

            <div className="space-y-3">
              {MOCK_API_KEYS.map((key) => (
                <div
                  key={key.id}
                  className="p-4 rounded-xl bg-white/5 backdrop-blur-md border border-white/10 hover:border-cyan-400/30 transition-all duration-300 group"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-medium text-white">{key.name}</h3>
                      <p className="text-xs font-mono text-gray-500 mt-1">
                        {key.prefix}••••••••
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleCopyKey(key.id)}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-cyan-400 hover:bg-cyan-400/10 transition-colors"
                        title="Copy API Key"
                      >
                        {copiedKey === key.id ? (
                          <CheckCircle2 className="w-4 h-4 text-green-400" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-400/10 transition-colors"
                        title="Revoke Key"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                    <span>Created: {key.created_at}</span>
                    <span>Last used: {key.last_used}</span>
                  </div>
                  <div className="mt-2">
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider",
                        key.status === "active"
                          ? "bg-green-500/20 text-green-400"
                          : "bg-gray-500/20 text-gray-400"
                      )}
                    >
                      {key.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* MCP Servers Section */}
          <div className="xl:col-span-1 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Server className="w-5 h-5 text-purple-400" />
                <h2 className="text-lg font-semibold text-white">MCP Servers</h2>
              </div>
              <Button
                size="sm"
                className="bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 border border-purple-500/30"
              >
                <Plus className="w-4 h-4 mr-1" />
                Add Server
              </Button>
            </div>

            <div className="space-y-3">
              {MOCK_MCP_SERVERS.map((server) => (
                <div
                  key={server.id}
                  className="p-4 rounded-xl bg-white/5 backdrop-blur-md border border-white/10 hover:border-purple-400/30 transition-all duration-300 group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className={cn(
                          "w-2.5 h-2.5 rounded-full",
                          server.status === "connected"
                            ? "bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.6)]"
                            : "bg-gray-500"
                        )}
                      />
                      <div>
                        <h3 className="font-medium text-white">{server.name}</h3>
                        <p className="text-xs font-mono text-gray-500 mt-0.5">
                          {server.url}
                        </p>
                      </div>
                    </div>
                    <button
                      className="p-1.5 rounded-lg text-gray-400 hover:text-purple-400 hover:bg-purple-400/10 transition-colors"
                      title="Configure"
                    >
                      <Settings className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex items-center justify-between mt-3">
                    <span className="text-xs text-gray-500">
                      {server.tools_count} tools available
                    </span>
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider",
                        server.status === "connected"
                          ? "bg-green-500/20 text-green-400"
                          : "bg-gray-500/20 text-gray-400"
                      )}
                    >
                      {server.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Channels Section */}
          <div className="xl:col-span-1 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageCircle className="w-5 h-5 text-amber-400" />
                <h2 className="text-lg font-semibold text-white">Channels</h2>
              </div>
              <Button
                size="sm"
                className="bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 border border-amber-500/30"
              >
                <Plus className="w-4 h-4 mr-1" />
                Add Channel
              </Button>
            </div>

            <div className="space-y-3">
              {MOCK_CHANNELS.map((channel) => {
                const ChannelIcon = channel.icon;
                return (
                  <div
                    key={channel.id}
                    className="p-4 rounded-xl bg-white/5 backdrop-blur-md border border-white/10 hover:border-amber-400/30 transition-all duration-300 group"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-white/5 border border-white/10">
                          <ChannelIcon className="w-5 h-5 text-amber-400" />
                        </div>
                        <div>
                          <h3 className="font-medium text-white">{channel.name}</h3>
                          <p className="text-xs text-gray-500 capitalize mt-0.5">
                            {channel.type}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider",
                            channel.status === "active"
                              ? "bg-green-500/20 text-green-400"
                              : channel.status === "pending"
                              ? "bg-amber-500/20 text-amber-400"
                              : "bg-gray-500/20 text-gray-400"
                          )}
                        >
                          {channel.status}
                        </span>
                        <button
                          className="p-1.5 rounded-lg text-gray-400 hover:text-amber-400 hover:bg-amber-400/10 transition-colors"
                          title="Configure"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Quick Stats */}
            <div className="mt-6 p-4 rounded-xl bg-gradient-to-br from-amber-500/10 to-purple-500/10 border border-white/10">
              <h3 className="text-sm font-medium text-white mb-3">Integration Status</h3>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold text-cyan-400">
                    {MOCK_API_KEYS.length}
                  </p>
                  <p className="text-xs text-gray-500">API Keys</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-purple-400">
                    {MOCK_MCP_SERVERS.filter((s) => s.status === "connected").length}
                  </p>
                  <p className="text-xs text-gray-500">Connected</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-amber-400">
                    {MOCK_CHANNELS.filter((c) => c.status === "active").length}
                  </p>
                  <p className="text-xs text-gray-500">Active</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Info Banner */}
        <div className="mt-8 p-6 rounded-2xl bg-white/5 backdrop-blur-md border border-white/10">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-cyan-400/10 border border-cyan-400/20">
              <Sparkles className="w-6 h-6 text-cyan-400" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-white">
                Expand Your Agent&apos;s Reach
              </h3>
              <p className="text-sm text-gray-400 mt-1">
                Connect your agents to external services through MCP servers, enable API access,
                or deploy communication channels to let users interact with your knowledge base.
              </p>
            </div>
            <Button className="bg-gradient-to-r from-cyan-500 to-purple-500 text-white hover:opacity-90">
              View Documentation
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
