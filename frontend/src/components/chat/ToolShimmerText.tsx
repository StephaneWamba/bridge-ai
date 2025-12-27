"use client";

import { cn } from "@/lib/utils";

interface ToolShimmerTextProps {
  text: string;
  className?: string;
  isActive?: boolean; // When true, apply shimmer effect
}

/**
 * Shimmering text component specifically for tool names.
 * Creates an indigo shimmer effect when the tool is in progress.
 */
export function ToolShimmerText({
  text,
  className,
  isActive = false,
}: ToolShimmerTextProps) {
  // Format tool name: snake_case to Title Case
  const formattedText = text
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");

  return (
    <span
      className={cn(
        "font-medium text-sm",
        isActive
          ? "bg-gradient-to-r from-indigo-500 via-indigo-300 to-indigo-500 bg-[length:200%_100%] animate-shimmer-text bg-clip-text text-transparent"
          : "text-gray-900 dark:text-gray-100",
        className
      )}
    >
      {formattedText}
    </span>
  );
}

