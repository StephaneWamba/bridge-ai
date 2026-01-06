"use client";

import { Sparkles, Settings, User, Bell, LogOut } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageSquare, BarChart3, Link2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

const navigation = [
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

interface HeaderProps {
  sessionId?: string | null;
  className?: string;
}

/**
 * Header component - top navigation bar with tabs (Option 2 design).
 */
export function Header({ sessionId, className }: HeaderProps) {
  const pathname = usePathname();
  const { logout } = useAuth();

  return (
    <header
      className={cn(
        "sticky top-0 z-30",
        "border-b border-gray-200 dark:border-gray-800",
        "bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl",
        className
      )}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
              BridgeAI
            </span>
          </Link>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive =
                pathname === item.href || pathname?.startsWith(item.href + "/");

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                    "relative",
                    isActive
                      ? "text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20"
                      : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                  {isActive && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600 dark:bg-indigo-400 rounded-full" />
                  )}
                </Link>
              );
            })}
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-2">
            {sessionId && (
              <div className="hidden sm:block text-xs text-gray-500 dark:text-gray-400 px-2 sm:px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 whitespace-nowrap">
                Session: {sessionId.slice(0, 8)}...
              </div>
            )}
            <ThemeToggle />
            <button
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5" />
            </button>
            <button
              onClick={logout}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
              aria-label="Logout"
              title="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

