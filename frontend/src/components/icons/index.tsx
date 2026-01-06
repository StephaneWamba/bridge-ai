/**
 * Icon mapping system - replaces emojis with lucide-react icons
 */

import {
  Users,
  User,
  Building2,
  Search,
  Edit,
  FileText,
  Mail,
  Send,
  Reply,
  Calendar,
  CalendarDays,
  MessageSquare,
  Zap,
  Settings,
  Plus,
  X,
  Check,
  AlertCircle,
  Loader2,
  ChevronRight,
  Copy,
  Clock,
  Wrench,
  Sparkles,
} from "lucide-react";
import { LucideIcon } from "lucide-react";

/**
 * Icon mapping for tools
 */
export const toolIcons: Record<string, LucideIcon> = {
  // HubSpot tools
  search_hubspot_contacts: Users,
  read_hubspot_contact: User,
  search_hubspot_companies: Building2,
  read_hubspot_company: Building2,
  update_hubspot_contact: Edit,
  create_hubspot_note: FileText,
  
  // Gmail tools
  read_gmail_emails: Mail,
  send_gmail_email: Send,
  reply_gmail_email: Reply,
  
  // Calendar tools
  list_calendar_events: CalendarDays,
  create_calendar_event: Calendar,
  
  // Default
  default: Wrench,
};

/**
 * Get icon component for a tool name
 */
export function getToolIcon(toolName: string): LucideIcon {
  return toolIcons[toolName] || toolIcons.default;
}

/**
 * Common icons used throughout the app
 */
export const icons = {
  message: MessageSquare,
  sparkle: Sparkles,
  zap: Zap,
  settings: Settings,
  plus: Plus,
  close: X,
  check: Check,
  error: AlertCircle,
  loading: Loader2,
  chevronRight: ChevronRight,
  copy: Copy,
  clock: Clock,
  wrench: Wrench,
};




