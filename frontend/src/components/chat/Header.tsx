"use client";

import { Sparkles, Settings, User } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { cn } from "@/lib/utils";

interface HeaderProps {
  sessionId?: string | null;
  className?: string;
}

/**
 * Header component - clean, minimal top navigation bar with indigo theme.
 */
export function Header({ sessionId, className }: HeaderProps) {
  return (
    <header
      className={cn(
        "sticky top-0 z-10",
        "border-b border-gray-200 dark:border-gray-700",
        "bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl",
        "px-6 py-4",
        className
      )}
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Logo & Branding */}
        <div className="flex items-center gap-2 sm:gap-3 min-w-0">
          <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 flex-shrink-0">
            <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
          </div>
          <div className="min-w-0">
            <h1 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-gray-100 truncate">
              BridgeAI Chat
            </h1>
            <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 hidden sm:block">
              Your AI assistant for integrations
            </p>
          </div>
        </div>

        {/* Right side actions */}
        <div className="flex items-center gap-2">
          {sessionId && (
            <div className="hidden sm:block text-xs text-gray-500 dark:text-gray-400 px-2 sm:px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 whitespace-nowrap">
              Session: {sessionId.slice(0, 8)}...
            </div>
          )}
          <ThemeToggle />
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

