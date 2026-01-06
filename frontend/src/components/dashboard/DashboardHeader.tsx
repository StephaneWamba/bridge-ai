"use client";

import { Bell, Settings, User } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";

interface DashboardHeaderProps {
  title?: string;
  className?: string;
}

export function DashboardHeader({ title = "Dashboard", className }: DashboardHeaderProps) {
  return (
    <header
      className={`sticky top-0 z-20 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border-b border-gray-200 dark:border-gray-800 ${className}`}
    >
      <div className="flex items-center justify-between px-6 py-4">
        {/* Page Title */}
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            {title}
          </h1>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <button
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
            aria-label="Notifications"
          >
            <Bell className="w-5 h-5" />
          </button>
          <button
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
            aria-label="Settings"
          >
            <Settings className="w-5 h-5" />
          </button>
          <button
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
            aria-label="User menu"
          >
            <User className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  );
}




