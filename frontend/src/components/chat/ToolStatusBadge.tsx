"use client";

import { Check, X, Loader2, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

export type ToolStatus = "pending" | "in-progress" | "success" | "error";

export type { ToolStatus as ToolStatusType };

interface ToolStatusBadgeProps {
  status: ToolStatus;
  className?: string;
}

export function ToolStatusBadge({ status, className }: ToolStatusBadgeProps) {
  const statusConfig = {
    pending: {
      icon: Clock,
      text: "Pending",
      className: "text-gray-500 dark:text-gray-400",
      bgClassName: "bg-gray-100 dark:bg-gray-800",
    },
    "in-progress": {
      icon: Loader2,
      text: "In Progress",
      className: "text-indigo-600 dark:text-indigo-400",
      bgClassName: "bg-indigo-100 dark:bg-indigo-900/20",
    },
    success: {
      icon: Check,
      text: "Complete",
      className: "text-green-600 dark:text-green-400",
      bgClassName: "bg-green-100 dark:bg-green-900/20",
    },
    error: {
      icon: X,
      text: "Error",
      className: "text-red-600 dark:text-red-400",
      bgClassName: "bg-red-100 dark:bg-red-900/20",
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium",
        config.bgClassName,
        config.className,
        className
      )}
    >
      {status === "in-progress" ? (
        <Icon className="w-3 h-3 animate-spin" />
      ) : (
        <Icon className="w-3 h-3" />
      )}
      <span>{config.text}</span>
    </div>
  );
}

