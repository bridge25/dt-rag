/**
 * SidebarSubmenu - Collapsible submenu component for sidebar navigation
 *
 * @CODE:FRONTEND-REDESIGN-001-SIDEBAR-SUBMENU
 */

"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface SubmenuItem {
  name: string;
  href: string;
  icon: React.ElementType;
}

interface SidebarSubmenuProps {
  title: string;
  icon: React.ElementType;
  items: SubmenuItem[];
  defaultOpen?: boolean;
}

export function SidebarSubmenu({
  title,
  icon: Icon,
  items,
  defaultOpen = false
}: SidebarSubmenuProps) {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(defaultOpen);

  // Check if any submenu item is active
  const hasActiveItem = items.some(item => pathname === item.href);

  // Auto-expand if an item is active
  const shouldBeOpen = isOpen || hasActiveItem;

  return (
    <div className="space-y-1">
      {/* Submenu Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center justify-between w-full gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-300",
          hasActiveItem
            ? "bg-white/5 text-white"
            : "text-white/60 hover:bg-white/5 hover:text-white"
        )}
      >
        <div className="flex items-center gap-3">
          <Icon className={cn(
            "h-5 w-5 transition-colors",
            hasActiveItem ? "text-cyan-400" : "text-white/60"
          )} />
          {title}
        </div>
        <div className={cn(
          "transition-transform duration-200",
          shouldBeOpen && "rotate-180"
        )}>
          <ChevronDown className="h-4 w-4" />
        </div>
      </button>

      {/* Submenu Items */}
      {shouldBeOpen && (
        <div className="pl-4 space-y-1 animate-in slide-in-from-top-2 fade-in duration-200">
          {items.map((item) => {
            const isActive = pathname === item.href;
            const ItemIcon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-300",
                  isActive
                    ? "bg-white/10 text-white shadow-glass border border-white/10"
                    : "text-white/50 hover:bg-white/5 hover:text-white hover:pl-5"
                )}
              >
                <ItemIcon className={cn(
                  "h-4 w-4 transition-colors",
                  isActive ? "text-cyan-400" : "text-white/50"
                )} />
                {item.name}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
