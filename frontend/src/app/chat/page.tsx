"use client";

import { useState, useRef, useEffect } from "react";
import { AlertCircle } from "lucide-react";
import { fetchAPI } from "@/lib/api/client";
import { ChatLayout } from "@/components/chat/ChatLayout";
import { WelcomeScreen } from "@/components/chat/WelcomeScreen";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import { LoadingBubble } from "@/components/chat/LoadingBubble";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  tool_calls?: ToolCall[];
  timestamp: Date;
}

interface Conversation {
  id: string;
  session_id: string;
  title: string;
  preview: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Fetch conversations on mount and when session changes
  useEffect(() => {
    const fetchConversations = async () => {
      setIsLoadingConversations(true);
      try {
        const response = await fetchAPI<{ conversations: Conversation[] }>(
          "/api/v1/agent/conversations?limit=50"
        );
        setConversations(response.conversations);
      } catch (error) {
        console.error("Failed to fetch conversations:", error);
        // Don't show error to user, just log it
      } finally {
        setIsLoadingConversations(false);
      }
    };

    fetchConversations();
  }, []);

  // Refresh conversations after sending a message
  useEffect(() => {
    if (sessionId) {
      const fetchConversations = async () => {
        try {
          const response = await fetchAPI<{ conversations: Conversation[] }>(
            "/api/v1/agent/conversations?limit=50"
          );
          setConversations(response.conversations);
        } catch (error) {
          console.error("Failed to refresh conversations:", error);
        }
      };
      fetchConversations();
    }
  }, [sessionId]);

  const handleSend = async (messageText?: string) => {
    const textToSend = messageText || input.trim();
    if (!textToSend || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: textToSend,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setError(null);
    setIsLoading(true);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };
      
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
      
      const response = await fetch(`${API_URL}/api/v1/agent/chat/stream`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          message: textToSend,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === "response") {
                  // Final response received
                  setSessionId(data.session_id);
                  const assistantMessage: Message = {
                    id: Date.now().toString(),
                    role: "assistant",
                    content: data.response,
                    timestamp: new Date(),
                  };
                  setMessages((prev) => [...prev, assistantMessage]);
                  setIsLoading(false);
                } else if (data.type === "error") {
                  throw new Error(data.error || "Unknown error");
                }
              } catch (e) {
                console.error("Error parsing SSE data:", e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
      setError(error instanceof Error ? error.message : "Failed to get response");
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: `Error: ${error instanceof Error ? error.message : "Failed to get response"}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      setIsLoading(false);
    }
  };

  // Transform conversations to session format for Sidebar
  const sessions = conversations.map((conv) => ({
    id: conv.session_id,
    title: conv.title,
    preview: conv.preview,
    timestamp: new Date(conv.updated_at),
    isActive: conv.session_id === sessionId,
  }));

  const handleNewSession = () => {
    setSessionId(null);
    setMessages([]);
    setError(null);
  };

  const handleSessionSelect = async (sessionIdParam: string) => {
    // Don't clear messages immediately - wait until we have new ones to avoid showing welcome screen
    setError(null);
    setIsLoading(true);

    try {
      // Fetch conversation messages from API
      const response = await fetchAPI<{
        session_id: string;
        messages: Array<{
          id: string;
          role: "user" | "assistant";
          content: string;
          timestamp: string;
        }>;
      }>(`/api/v1/agent/conversations/${sessionIdParam}/messages`);

      // Convert API messages to frontend format
      const loadedMessages: Message[] = response.messages.map((msg) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.timestamp),
      }));

      // Set session ID and messages together
      setSessionId(sessionIdParam);
      setMessages(loadedMessages);
    } catch (error) {
      console.error("Failed to load conversation:", error);
      setError("Failed to load conversation");
      // Still set the session ID even on error so user can try sending a message
      setSessionId(sessionIdParam);
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ChatLayout
      sessionId={sessionId}
      sessions={sessions}
      onSessionSelect={handleSessionSelect}
      onNewSession={handleNewSession}
      showSidebar={true}
    >
      {/* Messages Container */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-3 py-4 sm:px-4 sm:py-6 md:px-6"
      >
        <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">
          {messages.length === 0 && !isLoading && !sessionId && (
            <WelcomeScreen onExampleClick={handleSend} />
          )}

          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {isLoading && <LoadingBubble />}

          {error && (
            <div className="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 animate-in fade-in slide-in-from-bottom-2">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-red-900 dark:text-red-100">
                    Error
                  </p>
                  <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                    {error}
                  </p>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <ChatInput
        value={input}
        onChange={setInput}
        onSend={() => handleSend()}
        isLoading={isLoading}
      />
    </ChatLayout>
  );
}
