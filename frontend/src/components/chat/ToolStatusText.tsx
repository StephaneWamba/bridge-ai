"use client";

import { ToolShimmerText } from "./ToolShimmerText";
import { cn } from "@/lib/utils";

interface ToolStatusTextProps {
  toolName: string;
  status: "pending" | "in-progress" | "success" | "error";
  className?: string;
}

/**
 * Maps tool names to friendly user-facing phrases
 */
function getToolPhrase(toolName: string, status: "pending" | "in-progress" | "success" | "error"): string {
  const toolPhrases: Record<string, { inProgress: string; success: string; error: string }> = {
    // HubSpot tools
    "read_hubspot_contact": { 
      inProgress: "Reading contact...", 
      success: "Contact found", 
      error: "Failed to read contact" 
    },
    "search_hubspot_contacts": { 
      inProgress: "Searching for contacts...", 
      success: "Contacts found", 
      error: "Failed to search contacts" 
    },
    "read_hubspot_company": { 
      inProgress: "Reading company...", 
      success: "Company found", 
      error: "Failed to read company" 
    },
    "search_hubspot_companies": { 
      inProgress: "Searching for companies...", 
      success: "Companies found", 
      error: "Failed to search companies" 
    },
    "update_hubspot_contact": { 
      inProgress: "Updating contact...", 
      success: "Contact updated", 
      error: "Failed to update contact" 
    },
    "create_hubspot_note": { 
      inProgress: "Creating note...", 
      success: "Note created", 
      error: "Failed to create note" 
    },
    // Gmail tools
    "read_gmail_emails": { 
      inProgress: "Reading emails...", 
      success: "Emails loaded", 
      error: "Failed to read emails" 
    },
    "send_gmail_email": { 
      inProgress: "Sending email...", 
      success: "Email sent", 
      error: "Failed to send email" 
    },
    "reply_gmail_email": { 
      inProgress: "Replying to email...", 
      success: "Reply sent", 
      error: "Failed to reply" 
    },
    // Calendar tools
    "list_calendar_events": { 
      inProgress: "Checking calendar...", 
      success: "Calendar events loaded", 
      error: "Failed to load calendar" 
    },
    "create_calendar_event": { 
      inProgress: "Creating calendar event...", 
      success: "Event created", 
      error: "Failed to create event" 
    },
    "get_calendar_event": { 
      inProgress: "Getting event details...", 
      success: "Event details loaded", 
      error: "Failed to get event" 
    },
  };

  const phrases = toolPhrases[toolName] || {
    inProgress: `Executing ${toolName.replace(/_/g, " ")}...`,
    success: `${toolName.replace(/_/g, " ")} completed`,
    error: `Failed to execute ${toolName.replace(/_/g, " ")}`,
  };

  if (status === "in-progress" || status === "pending") {
    return phrases.inProgress;
  } else if (status === "error") {
    return phrases.error;
  } else {
    return phrases.success;
  }
}

/**
 * Simple tool status text component showing friendly phrases with shimmer effect
 */
export function ToolStatusText({ toolName, status, className }: ToolStatusTextProps) {
  const phrase = getToolPhrase(toolName, status);
  const isActive = status === "in-progress" || status === "pending";

  return (
    <div className={cn("text-xs text-gray-600 dark:text-gray-400 mt-2", className)}>
      <ToolShimmerText text={phrase} isActive={isActive} />
    </div>
  );
}
