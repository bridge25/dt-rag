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
    <div className="flex h-full w-64 flex-col bg-graySidebar text-white">
      <div className="flex items-center justify-center border-b border-white/10 p-6">
        <h1 className="text-2xl font-bold">DT-RAG</h1>
      </div>

      <div className="border-b border-white/10 p-6">
        <div className="flex flex-col items-center">
          <div className="relative">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white/10">
              <User className="h-8 w-8 text-white" />
            </div>
            <div className="absolute -bottom-1 -right-1 h-4 w-4 rounded-full border-2 border-graySidebar bg-green-500"></div>
          </div>
          <h3 className="mt-3 font-semibold">Admin User</h3>
          <p className="text-sm text-white/70">System Administrator</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all",
                isActive
                  ? "bg-white/20 text-white shadow-sm"
                  : "text-white/80 hover:bg-white/10 hover:text-white"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 p-4">
        <button className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-white/80 transition-all hover:bg-white/10 hover:text-white">
          <LogOut className="h-5 w-5" />
          Sign Out
        </button>
      </div>
    </div>
  );
}
