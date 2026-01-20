"use client";

import { ReactNode, useState } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatLayoutProps {
  children: ReactNode;
  sessionId?: string | null;
  sessions?: Array<{
    id: string;
    title: string;
    preview: string;
    timestamp: Date;
    isActive?: boolean;
  }>;
  onSessionSelect?: (sessionId: string) => void;
  onNewSession?: () => void;
  showSidebar?: boolean;
}

/**
 * ChatLayout component - Linear-inspired split view layout.
 * Sidebar + main chat area with indigo theme.
 * Responsive: Sidebar becomes a drawer on mobile.
 */
export function ChatLayout({
  children,
  sessionId,
  sessions = [],
  onSessionSelect,
  onNewSession,
  showSidebar = true,
}: ChatLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <Header sessionId={sessionId} />

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Mobile Sidebar Overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        {showSidebar && (
          <>
            {/* Desktop Sidebar */}
            <aside className={cn(
              "hidden lg:flex lg:flex-col lg:border-r lg:border-gray-200 lg:dark:border-gray-700",
              "transition-all duration-300 ease-in-out",
              sidebarCollapsed ? "lg:w-[60px]" : "lg:w-[280px]"
            )}>
              <Sidebar
                sessions={sessions}
                activeSessionId={sessionId || undefined}
                onSessionSelect={(id) => {
                  onSessionSelect?.(id);
                  setSidebarOpen(false); // Close on mobile after selection
                }}
                onNewSession={() => {
                  onNewSession?.();
                  setSidebarOpen(false); // Close on mobile after new session
                }}
                collapsed={sidebarCollapsed}
                onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
              />
            </aside>

            {/* Mobile Sidebar Drawer */}
            <aside
              className={cn(
                "fixed top-0 left-0 z-50 h-full w-[280px] transform transition-transform duration-300 ease-in-out lg:hidden",
                sidebarOpen ? "translate-x-0" : "-translate-x-full"
              )}
            >
              <Sidebar
                sessions={sessions}
                activeSessionId={sessionId || undefined}
                onSessionSelect={(id) => {
                  onSessionSelect?.(id);
                  setSidebarOpen(false);
                }}
                onNewSession={() => {
                  onNewSession?.();
                  setSidebarOpen(false);
                }}
              />
            </aside>
          </>
        )}

        {/* Chat Area */}
        <main className="flex-1 flex flex-col overflow-hidden bg-white dark:bg-gray-900 relative">
          {/* Mobile Sidebar Toggle Button */}
          {showSidebar && (
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className={cn(
                "lg:hidden fixed top-20 left-4 z-30",
                "p-2 rounded-lg",
                "bg-white dark:bg-gray-800",
                "border border-gray-200 dark:border-gray-700",
                "text-gray-600 dark:text-gray-400",
                "hover:bg-gray-100 dark:hover:bg-gray-700",
                "shadow-lg",
                "transition-colors",
                "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              )}
              aria-label="Toggle sidebar"
            >
              {sidebarOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>
          )}

          {children}
        </main>
      </div>
    </div>
  );
}
