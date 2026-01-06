"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageSquare, BarChart3, Link2, Settings, Sparkles, Home } from "lucide-react";
import Image from "next/image";
import { cn } from "@/lib/utils";

const navigation = [
  {
    name: "Home",
    href: "/",
    icon: Home,
  },
  {
    name: "Chat",
    href: "/chat",
    icon: MessageSquare,
  },
  {
    name: "Insights",
    href: "/dashboard/insights",
    icon: BarChart3,
  },
  {
    name: "Integrations",
    href: "/integrations",
    icon: Link2,
  },
  {
    name: "Settings",
    href: "/dashboard/settings",
    icon: Settings,
  },
];

interface DashboardSidebarProps {
  className?: string;
}

export function DashboardSidebar({ className }: DashboardSidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-30 h-full w-60 flex flex-col",
        "bg-white dark:bg-gray-900",
        "border-r border-gray-200 dark:border-gray-800",
        className
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-200 dark:border-gray-800">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
          BridgeAI
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400"
                  : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-100"
              )}
            >
              <Icon className="w-5 h-5" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom Section - Settings or Profile could go here */}
      <div className="px-3 py-4 border-t border-gray-200 dark:border-gray-800">
        {/* Future: User profile or additional actions */}
      </div>
    </aside>
  );
}

