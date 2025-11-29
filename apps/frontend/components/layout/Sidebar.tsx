/**
 * Sidebar navigation component
 * Phase 2: System submenu 적용
 * Phase 3: i18n 지원 추가
 *
 * @CODE:FRONTEND-REDESIGN-001-SIDEBAR
 * @CODE:FRONTEND-REDESIGN-001-I18N
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,  // Chat 아이콘 (Search 대체)
  Network,
  Bot,
  Plug,           // Connect 아이콘
  Workflow,
  Activity,
  UserCheck,
  User,
  LogOut,
  Settings,       // System 서브메뉴 아이콘
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { SidebarSubmenu } from "./SidebarSubmenu";
import { LanguageSwitcher } from "@/components/ui/language-switcher";
import { useTranslation } from "@/lib/i18n";

// Navigation item type
interface NavItem {
  nameKey: string;
  href: string;
  icon: LucideIcon;
}

// 메인 네비게이션 (이벤트 플로우 순서)
// Phase 3: Documents를 Taxonomy의 Import Knowledge로 통합
// Phase 4: Connect 페이지 추가
const mainNavigation: NavItem[] = [
  { nameKey: "nav.dashboard", href: "/", icon: LayoutDashboard },
  { nameKey: "nav.taxonomy", href: "/taxonomy", icon: Network },      // 시작점: 지식 구조화 (Import Knowledge FAB 포함)
  { nameKey: "nav.agents", href: "/agents", icon: Bot },               // 탄생: 에이전트
  { nameKey: "nav.chat", href: "/chat", icon: MessageSquare },         // 대화: 채팅 인터페이스
  { nameKey: "nav.connect", href: "/connect", icon: Plug },            // 연결: 외부 통합
];

// System 서브메뉴 아이템
const systemNavigation: NavItem[] = [
  { nameKey: "nav.ingestion", href: "/pipeline", icon: Workflow },
  { nameKey: "nav.analytics", href: "/hitl", icon: UserCheck },
  { nameKey: "nav.system", href: "/monitoring", icon: Activity },
];

export function Sidebar() {
  const pathname = usePathname();
  const { t } = useTranslation();

  // Translate system navigation items for submenu
  const translatedSystemNav = systemNavigation.map(item => ({
    name: t(item.nameKey),
    href: item.href,
    icon: item.icon,
  }));

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
          <h3 className="mt-3 font-semibold text-white group-hover:text-blue-300 transition-colors">
            {t("user.adminUser")}
          </h3>
          <p className="text-xs text-white/50">{t("user.systemAdministrator")}</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-4 overflow-y-auto custom-scrollbar">
        {/* 메인 네비게이션 */}
        {mainNavigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.nameKey}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-300",
                isActive
                  ? "bg-white/10 text-white shadow-glass border border-white/10"
                  : "text-white/60 hover:bg-white/5 hover:text-white hover:pl-5"
              )}
            >
              <Icon className={cn("h-5 w-5 transition-colors", isActive ? "text-cyan-400" : "text-white/60 group-hover:text-white")} />
              {t(item.nameKey)}
            </Link>
          );
        })}

        {/* 구분선 */}
        <div className="my-3 border-t border-white/5" />

        {/* System 서브메뉴 */}
        <SidebarSubmenu
          title={t("nav.system")}
          icon={Settings}
          items={translatedSystemNav}
          defaultOpen={false}
        />
      </nav>

      {/* Language Switcher & Sign Out */}
      <div className="border-t border-white/10 p-4 space-y-3">
        <LanguageSwitcher />
        <button className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-white/60 transition-all hover:bg-red-500/10 hover:text-red-400 hover:border hover:border-red-500/20">
          <LogOut className="h-5 w-5" />
          {t("common.signOut")}
        </button>
      </div>
    </div>
  );
}
