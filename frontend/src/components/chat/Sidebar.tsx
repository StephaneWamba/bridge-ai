"use client";

import { useState } from "react";
import { MessageSquare, Plus, Search, X, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface Session {
  id: string;
  title: string;
  preview: string;
  timestamp: Date;
  isActive?: boolean;
}

interface SidebarProps {
  sessions?: Session[];
  activeSessionId?: string | null;
  onSessionSelect?: (sessionId: string) => void;
  onNewSession?: () => void;
  className?: string;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

/**
 * Sidebar component for session management.
 * Displays list of conversations with search functionality.
 */
export function Sidebar({
  sessions = [],
  activeSessionId,
  onSessionSelect,
  onNewSession,
  className,
  collapsed = false,
  onToggleCollapse,
}: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredSessions = sessions.filter((session) =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    session.preview.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMinutes < 60) {
      return `${diffMinutes}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <aside
      className={cn(
        "flex flex-col",
        "bg-white dark:bg-gray-900",
        "border-r border-gray-200 dark:border-gray-700",
        collapsed ? "w-[60px]" : "w-[280px]",
        "transition-all duration-300",
        className
      )}
    >
      {/* Header */}
      <div className="p-3 sm:p-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
        {!collapsed && (
          <button
            onClick={onNewSession}
            className={cn(
              "flex-1 flex items-center justify-center gap-2",
              "px-3 sm:px-4 py-2 sm:py-2.5 rounded-lg",
              "bg-indigo-500 hover:bg-indigo-600",
              "text-white text-sm sm:text-base font-medium",
              "shadow-md shadow-indigo-500/20",
              "transition-all duration-200",
              "hover:scale-[1.02] active:scale-[0.98]",
              "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            )}
          >
            <Plus className="w-4 h-4" />
            <span className="hidden sm:inline">New Conversation</span>
            <span className="sm:hidden">New</span>
          </button>
        )}
        {collapsed && (
          <button
            onClick={onNewSession}
            className={cn(
              "w-full flex items-center justify-center",
              "p-2.5 rounded-lg",
              "bg-indigo-500 hover:bg-indigo-600",
              "text-white",
              "shadow-md shadow-indigo-500/20",
              "transition-all duration-200",
              "hover:scale-[1.02] active:scale-[0.98]",
              "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            )}
            title="New Conversation"
          >
            <Plus className="w-5 h-5" />
          </button>
        )}
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className={cn(
              "p-1.5 rounded-lg",
              "text-gray-500 dark:text-gray-400",
              "hover:bg-gray-100 dark:hover:bg-gray-800",
              "transition-colors",
              "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2",
              collapsed && "mx-auto"
            )}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </button>
        )}
      </div>

      {/* Search */}
      {!collapsed && (
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={cn(
                "w-full pl-10 pr-8 py-2 rounded-lg",
                "bg-gray-100 dark:bg-gray-800",
                "border border-gray-200 dark:border-gray-700",
                "text-sm text-gray-900 dark:text-gray-100",
                "placeholder-gray-400 dark:placeholder-gray-500",
                "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500",
                "transition-all"
              )}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        {filteredSessions.length === 0 ? (
          !collapsed && (
            <div className="p-8 text-center">
              <MessageSquare className="w-12 h-12 text-gray-300 dark:text-gray-700 mx-auto mb-3" />
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {searchQuery ? "No conversations found" : "No conversations yet"}
              </p>
              {!searchQuery && (
                <button
                  onClick={onNewSession}
                  className="mt-4 text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  Start a conversation
                </button>
              )}
            </div>
          )
        ) : (
          <div className={cn("space-y-1", collapsed ? "p-2" : "p-2")}>
            {filteredSessions.map((session) => {
              const isActive = session.id === activeSessionId;
              // Clean up title and preview - remove any JSON artifacts
              const cleanTitle = session.title && !session.title.startsWith("{") 
                ? session.title 
                : "New Conversation";
              const cleanPreview = session.preview && !session.preview.startsWith("{") 
                ? session.preview 
                : "";
              
              return (
                <button
                  key={session.id}
                  onClick={() => onSessionSelect?.(session.id)}
                  className={cn(
                    "w-full rounded-lg",
                    "transition-all duration-200",
                    "group",
                    collapsed ? "p-2 flex items-center justify-center" : "text-left p-3",
                    isActive
                      ? "bg-indigo-100 dark:bg-indigo-900/20 border-l-3 border-indigo-500"
                      : "hover:bg-gray-100 dark:hover:bg-gray-800"
                  )}
                  title={collapsed ? cleanTitle : undefined}
                >
                  {collapsed ? (
                    <MessageSquare
                      className={cn(
                        "w-5 h-5",
                        isActive
                          ? "text-indigo-600 dark:text-indigo-400"
                          : "text-gray-400 dark:text-gray-500"
                      )}
                    />
                  ) : (
                    <div className="flex items-start gap-3">
                      <MessageSquare
                        className={cn(
                          "w-4 h-4 mt-0.5 flex-shrink-0",
                          isActive
                            ? "text-indigo-600 dark:text-indigo-400"
                            : "text-gray-400 dark:text-gray-500"
                        )}
                      />
                      <div className="flex-1 min-w-0">
                        <div
                          className={cn(
                            "font-medium text-sm truncate",
                            isActive
                              ? "text-indigo-700 dark:text-indigo-300"
                              : "text-gray-900 dark:text-gray-100"
                          )}
                        >
                          {cleanTitle}
                        </div>
                        {cleanPreview && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                            {cleanPreview}
                          </div>
                        )}
                        <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {formatTimestamp(session.timestamp)}
                        </div>
                      </div>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </aside>
  );
}

