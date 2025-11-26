/**
 * Sidebar navigation component
 *
 * @CODE:FRONTEND-001
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  FileText,
  Network,
  Bot,
  Workflow,
  Activity,
  UserCheck,
  User,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Search", href: "/search", icon: Search },
  { name: "Documents", href: "/documents", icon: FileText },
  { name: "Taxonomy", href: "/taxonomy", icon: Network },
  { name: "Agents", href: "/agents", icon: Bot },
  { name: "Pipeline", href: "/pipeline", icon: Workflow },
  { name: "HITL Review", href: "/hitl", icon: UserCheck },
  { name: "Monitoring", href: "/monitoring", icon: Activity },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col bg-glass border-r border-white/10 text-white backdrop-blur-xl">
      <div className="flex items-center justify-center border-b border-white/10 p-6">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          DT-RAG
        </h1>
      </div>

      <div className="border-b border-white/10 p-6">
        <div className="flex flex-col items-center group cursor-pointer">
          <div className="relative transition-transform duration-300 group-hover:scale-105">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white/5 border border-white/10 shadow-glass">
              <User className="h-8 w-8 text-blue-300" />
            </div>
            <div className="absolute -bottom-1 -right-1 h-4 w-4 rounded-full border-2 border-dark-navy bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]"></div>
          </div>
          <h3 className="mt-3 font-semibold text-white group-hover:text-blue-300 transition-colors">Admin User</h3>
          <p className="text-xs text-white/50">System Administrator</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-4 overflow-y-auto custom-scrollbar">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-300",
                isActive
                  ? "bg-white/10 text-white shadow-glass border border-white/10"
                  : "text-white/60 hover:bg-white/5 hover:text-white hover:pl-5"
              )}
            >
              <Icon className={cn("h-5 w-5 transition-colors", isActive ? "text-blue-400" : "text-white/60 group-hover:text-white")} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 p-4">
        <button className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-white/60 transition-all hover:bg-red-500/10 hover:text-red-400 hover:border hover:border-red-500/20">
          <LogOut className="h-5 w-5" />
          Sign Out
        </button>
      </div>
    </div>
  );
}
