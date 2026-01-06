"use client";

import { useEffect, useState } from "react";
import { MessageSquare, Link2, BarChart3, TrendingUp, Activity, Clock } from "lucide-react";
import { fetchAPI } from "@/lib/api/client";

interface ConversationStats {
  total: number;
  thisWeek: number;
  thisMonth: number;
}

interface IntegrationStats {
  hubspot: {
    connected: boolean;
    lastUsed?: string;
  };
  google: {
    connected: boolean;
    lastUsed?: string;
  };
}

interface InsightsData {
  conversations: ConversationStats;
  integrations: IntegrationStats;
  totalMessages: number;
  activeIntegrations: number;
}

export default function InsightsPage() {
  const [data, setData] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInsights();
  }, []);

  const loadInsights = async () => {
    try {
      // Fetch conversations
      const conversationsResponse = await fetchAPI<{ conversations: any[] }>(
        "/api/v1/agent/conversations?limit=100"
      );

      // Fetch integration status
      const [hubspotStatus, googleStatus] = await Promise.all([
        fetchAPI<{ connected: boolean; is_active?: boolean }>(
          "/api/v1/integrations/hubspot/status"
        ).catch(() => ({ connected: false })),
        fetchAPI<{ gmail: { connected: boolean }; calendar: { connected: boolean } }>(
          "/api/v1/integrations/google/status"
        ).catch(() => ({ gmail: { connected: false }, calendar: { connected: false } })),
      ]);

      const conversations = conversationsResponse.conversations || [];
      const now = new Date();
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

      const thisWeek = conversations.filter((conv) => {
        const updated = new Date(conv.updated_at);
        return updated >= weekAgo;
      }).length;

      const thisMonth = conversations.filter((conv) => {
        const updated = new Date(conv.updated_at);
        return updated >= monthAgo;
      }).length;

      const totalMessages = conversations.reduce((sum, conv) => sum + (conv.message_count || 0), 0);

      const activeIntegrations = [
        hubspotStatus.connected,
        googleStatus.gmail?.connected || googleStatus.calendar?.connected,
      ].filter(Boolean).length;

      setData({
        conversations: {
          total: conversations.length,
          thisWeek,
          thisMonth,
        },
        integrations: {
          hubspot: {
            connected: hubspotStatus.connected || false,
          },
          google: {
            connected: (googleStatus.gmail?.connected || googleStatus.calendar?.connected) || false,
          },
        },
        totalMessages,
        activeIntegrations,
      });
    } catch (error) {
      console.error("Failed to load insights:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Insights
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Unable to load insights data.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Insights & Analytics
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Track your usage, integrations, and activity
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Total Conversations */}
        <StatCard
          title="Total Conversations"
          value={data.conversations.total}
          icon={MessageSquare}
          trend={`${data.conversations.thisWeek} this week`}
          trendUp={data.conversations.thisWeek > 0}
        />

        {/* Total Messages */}
        <StatCard
          title="Total Messages"
          value={data.totalMessages}
          icon={Activity}
          trend={`Across ${data.conversations.total} conversations`}
        />

        {/* Active Integrations */}
        <StatCard
          title="Active Integrations"
          value={data.activeIntegrations}
          icon={Link2}
          trend={`${data.integrations.hubspot.connected ? 'HubSpot' : ''}${data.integrations.hubspot.connected && data.integrations.google.connected ? ', ' : ''}${data.integrations.google.connected ? 'Google' : ''}`}
        />

        {/* This Month */}
        <StatCard
          title="This Month"
          value={data.conversations.thisMonth}
          icon={TrendingUp}
          trend={`${data.conversations.thisWeek} this week`}
          trendUp={data.conversations.thisMonth > 0}
        />
      </div>

      {/* Integration Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <IntegrationCard
          name="HubSpot"
          connected={data.integrations.hubspot.connected}
        />
        <IntegrationCard
          name="Google (Gmail & Calendar)"
          connected={data.integrations.google.connected}
        />
      </div>

      {/* Activity Timeline */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Recent Activity
          </h2>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          Activity timeline coming soon. This will show recent conversations, integration events, and system activity.
        </p>
      </div>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  trend?: string;
  trendUp?: boolean;
}

function StatCard({ title, value, icon: Icon, trend, trendUp }: StatCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/20">
          <Icon className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
        </div>
      </div>
      <div>
        <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
          {title}
        </p>
        <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          {value.toLocaleString()}
        </p>
        {trend && (
          <p
            className={`text-sm ${
              trendUp !== undefined
                ? trendUp
                  ? "text-green-600 dark:text-green-400"
                  : "text-gray-500 dark:text-gray-400"
                : "text-gray-500 dark:text-gray-400"
            }`}
          >
            {trend}
          </p>
        )}
      </div>
    </div>
  );
}

interface IntegrationCardProps {
  name: string;
  connected: boolean;
}

function IntegrationCard({ name, connected }: IntegrationCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
            {name}
          </h3>
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                connected
                  ? "bg-green-500"
                  : "bg-gray-400"
              }`}
            />
            <span
              className={`text-sm ${
                connected
                  ? "text-green-600 dark:text-green-400"
                  : "text-gray-500 dark:text-gray-400"
              }`}
            >
              {connected ? "Connected" : "Not Connected"}
            </span>
          </div>
        </div>
        <Link2
          className={`w-5 h-5 ${
            connected
              ? "text-green-600 dark:text-green-400"
              : "text-gray-400"
          }`}
        />
      </div>
    </div>
  );
}
