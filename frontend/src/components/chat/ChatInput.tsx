"use client";

import { useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  isLoading: boolean;
  placeholder?: string;
}

/**
 * ChatInput component with indigo theme and fixed contrast.
 * Dark text on light background for readability.
 */
export function ChatInput({
  value,
  onChange,
  onSend,
  isLoading,
  placeholder = "Type your message...",
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !isLoading) {
        onSend();
      }
    }
  };

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-3 py-3 sm:px-4 sm:py-4 md:px-6">
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              rows={1}
              disabled={isLoading}
              className={cn(
                "w-full px-4 py-3 pr-12 rounded-xl",
                "bg-white dark:bg-gray-800",
                "border border-gray-200 dark:border-gray-700",
                "text-gray-900 dark:text-gray-100",
                "placeholder-gray-400 dark:placeholder-gray-500",
                "resize-none focus:outline-none",
                "focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500",
                "transition-all duration-150",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "min-h-[56px] max-h-[200px]"
              )}
              style={{
                minHeight: "56px",
                maxHeight: "200px",
              }}
            />
            {/* Keyboard hints - hidden on mobile */}
            <div className="absolute right-3 bottom-3 hidden md:flex items-center gap-2 text-xs text-gray-400 dark:text-gray-500">
              <kbd className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                Enter
              </kbd>
              <span>to send</span>
              <kbd className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                Shift+Enter
              </kbd>
              <span>for new line</span>
            </div>
          </div>
          <button
            onClick={onSend}
            disabled={!value.trim() || isLoading}
            className={cn(
              "flex-shrink-0 px-6 py-3 rounded-xl",
              "bg-indigo-500 hover:bg-indigo-600",
              "text-white font-medium",
              "shadow-lg shadow-indigo-500/20",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-all duration-200",
              "hover:scale-105 active:scale-95 disabled:hover:scale-100",
              "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            )}
          >
            {isLoading ? (
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Sending...</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span>Send</span>
                <Send className="w-4 h-4" />
              </div>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
