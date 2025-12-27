"use client";

import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * LoadingBubble component with "Thinking..." shimmering text.
 * Shows AI thinking state with indigo-themed design.
 */
export function LoadingBubble() {
  return (
    <div className="flex gap-4 justify-start animate-in fade-in slide-in-from-bottom-2 duration-300">
      {/* AI Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
        <Sparkles className="w-4 h-4 text-white" />
      </div>

      {/* Message Bubble with "Thinking..." shimmering text */}
      <div className="flex flex-col items-start max-w-[85%] md:max-w-2xl">
        <div className="relative rounded-2xl px-5 py-4 bg-white dark:bg-gray-800/90 text-gray-900 dark:text-gray-100 border border-gray-200/50 dark:border-gray-700/50 shadow-sm backdrop-blur-sm">
          <span className="bg-gradient-to-r from-indigo-500 via-indigo-300 to-indigo-500 bg-[length:200%_100%] animate-shimmer-text bg-clip-text text-transparent font-medium">
            Thinking...
          </span>
        </div>
      </div>
    </div>
  );
}
