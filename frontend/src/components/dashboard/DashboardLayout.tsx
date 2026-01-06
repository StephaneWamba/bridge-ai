"use client";

import { ReactNode } from "react";
import { TopNavigation } from "./TopNavigation";
import { cn } from "@/lib/utils";

interface DashboardLayoutProps {
  children: ReactNode;
  title?: string;
  hideHeader?: boolean;
}

export function DashboardLayout({ children, title, hideHeader = false }: DashboardLayoutProps) {
  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-950 overflow-hidden">
      {/* Top Navigation - Hidden for chat page (chat has its own header) */}
      {!hideHeader && <TopNavigation />}

      {/* Main Content Area */}
      <main className={cn(
        "flex-1 overflow-y-auto",
        hideHeader ? "bg-gray-50 dark:bg-gray-950" : "bg-white dark:bg-gray-900"
      )}>
        {children}
      </main>
    </div>
  );
}

