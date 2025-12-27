"use client";

import { Sparkles, User, Copy, Check } from "lucide-react";
import { useState } from "react";
import { formatDistanceToNow } from "@/lib/utils/date";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        "flex gap-4 group",
        isUser ? "justify-end" : "justify-start",
        "animate-in fade-in slide-in-from-bottom-2 duration-300"
      )}
    >
      {/* AI Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
      )}

      <div
        className={cn(
          "flex flex-col",
          isUser ? "items-end" : "items-start",
          "max-w-[90%] sm:max-w-[85%] md:max-w-2xl"
        )}
      >
        {/* Message Bubble */}
        <div
          className={cn(
            "relative rounded-2xl px-5 py-4",
            isUser
              ? "bg-indigo-500 text-white shadow-lg shadow-indigo-500/30"
              : "bg-white dark:bg-gray-800/90 text-gray-900 dark:text-gray-100 border border-gray-200/50 dark:border-gray-700/50 shadow-sm backdrop-blur-sm"
          )}
        >
          {/* Content */}
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {isUser ? (
              <div className="text-white">
                <ReactMarkdown 
                  className="m-0 [&_p]:whitespace-pre-wrap [&_p]:break-words"
                  components={{
                    p: ({ children }) => <p style={{ whiteSpace: 'pre-wrap', margin: 0, wordBreak: 'break-word' }}>{children}</p>,
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            ) : (
              <div className="text-gray-900 dark:text-gray-100">
                {message.content && (
                  <ReactMarkdown 
                    className="m-0 [&_p]:whitespace-pre-wrap [&_p]:break-words"
                    components={{
                      p: ({ children }) => <p style={{ whiteSpace: 'pre-wrap', margin: 0, wordBreak: 'break-word' }}>{children}</p>,
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                )}
              </div>
            )}
          </div>

          {/* Copy Button (hover only for AI messages) */}
          {!isUser && (
            <button
              onClick={handleCopy}
              className={cn(
                "absolute -top-2 -right-2",
                "w-8 h-8 rounded-lg",
                "bg-gray-100 dark:bg-gray-700",
                "border border-gray-200 dark:border-gray-600",
                "flex items-center justify-center",
                "opacity-0 group-hover:opacity-100",
                "transition-opacity duration-200",
                "hover:bg-gray-200 dark:hover:bg-gray-600",
                "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              )}
              aria-label="Copy message"
            >
              {copied ? (
                <Check className="w-4 h-4 text-green-600 dark:text-green-400" />
              ) : (
                <Copy className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              )}
            </button>
          )}
        </div>

        {/* Timestamp */}
        <div
          className={cn(
            "mt-2 px-2 text-xs text-gray-500 dark:text-gray-400",
            "opacity-0 group-hover:opacity-100 transition-opacity",
            isUser ? "text-right" : "text-left"
          )}
        >
          {formatDistanceToNow(message.timestamp, { addSuffix: true })}
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-400 dark:bg-gray-600 flex items-center justify-center shadow-md">
          <User className="w-4 h-4 text-white" />
        </div>
      )}
    </div>
  );
}
