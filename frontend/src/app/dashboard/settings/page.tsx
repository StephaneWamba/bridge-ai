"use client";

import { useState, useEffect } from "react";
import { User, Bell, Key, Shield, Trash2, Download, Save, Link2 } from "lucide-react";
import { useTheme } from "next-themes";
import { fetchAPI } from "@/lib/api/client";
import Link from "next/link";

interface IntegrationStatus {
  hubspot: {
    connected: boolean;
    is_active?: boolean;
  };
  google: {
    gmail: {
      connected: boolean;
      is_active: boolean;
    };
    calendar: {
      connected: boolean;
      is_active: boolean;
    };
  };
}

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setMounted(true);
    loadIntegrationStatus();
  }, []);

  const loadIntegrationStatus = async () => {
    try {
      const [hubspot, google] = await Promise.all([
        fetchAPI<{ connected: boolean; is_active?: boolean }>(
          "/api/v1/integrations/hubspot/status"
        ).catch(() => ({ connected: false })),
        fetchAPI<{ gmail: { connected: boolean; is_active: boolean }; calendar: { connected: boolean; is_active: boolean } }>(
          "/api/v1/integrations/google/status"
        ).catch(() => ({ gmail: { connected: false, is_active: false }, calendar: { connected: false, is_active: false } })),
      ]);

      setIntegrationStatus({
        hubspot: hubspot || { connected: false },
        google: google || { gmail: { connected: false, is_active: false }, calendar: { connected: false, is_active: false } },
      });
    } catch (error) {
      console.error("Failed to load integration status:", error);
    } finally {
      setLoading(false);
    }
  };

  if (!mounted) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Settings
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Manage your account preferences and integrations
        </p>
      </div>

      <div className="space-y-6">
        {/* Profile Settings */}
        <SettingsSection
          icon={User}
          title="Profile Settings"
          description="Manage your account information"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Display Name
              </label>
              <input
                type="text"
                defaultValue="BridgeAI User"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Email
              </label>
              <input
                type="email"
                defaultValue="user@example.com"
                disabled
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-500 dark:text-gray-400 cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Email cannot be changed
              </p>
            </div>
            <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium flex items-center gap-2">
              <Save className="w-4 h-4" />
              Save Changes
            </button>
          </div>
        </SettingsSection>

        {/* Theme Preferences */}
        <SettingsSection
          icon={User}
          title="Theme Preferences"
          description="Customize your appearance"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Color Theme
              </label>
              <div className="flex gap-3">
                <button
                  onClick={() => setTheme("light")}
                  className={`px-4 py-2 rounded-lg border-2 transition-all ${
                    theme === "light"
                      ? "border-indigo-600 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400"
                      : "border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-400 dark:hover:border-gray-500"
                  }`}
                >
                  Light
                </button>
                <button
                  onClick={() => setTheme("dark")}
                  className={`px-4 py-2 rounded-lg border-2 transition-all ${
                    theme === "dark"
                      ? "border-indigo-600 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400"
                      : "border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-400 dark:hover:border-gray-500"
                  }`}
                >
                  Dark
                </button>
                <button
                  onClick={() => setTheme("system")}
                  className={`px-4 py-2 rounded-lg border-2 transition-all ${
                    theme === "system"
                      ? "border-indigo-600 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400"
                      : "border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-400 dark:hover:border-gray-500"
                  }`}
                >
                  System
                </button>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Current theme: <span className="font-medium">{theme || "system"}</span>
              </p>
            </div>
          </div>
        </SettingsSection>

        {/* Notification Settings */}
        <SettingsSection
          icon={Bell}
          title="Notification Settings"
          description="Control how you receive updates"
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Email Notifications
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Receive email updates about your account
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked className="sr-only peer" />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 dark:peer-focus:ring-indigo-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-indigo-600"></div>
              </label>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Integration Alerts
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Get notified when integrations need attention
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked className="sr-only peer" />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 dark:peer-focus:ring-indigo-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-indigo-600"></div>
              </label>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Activity Notifications
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Receive updates about AI agent activity
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 dark:peer-focus:ring-indigo-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-indigo-600"></div>
              </label>
            </div>
          </div>
        </SettingsSection>

        {/* API Keys & Tokens */}
        <SettingsSection
          icon={Key}
          title="API Keys & Tokens"
          description="Manage your API access and security"
        >
          <div className="space-y-4">
            {loading ? (
              <div className="animate-pulse space-y-3">
                <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded-lg" />
                <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded-lg" />
              </div>
            ) : (
              <>
                {integrationStatus?.hubspot.connected && (
                  <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        HubSpot Integration
                      </p>
                      <span className="px-2 py-1 text-xs font-medium bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-400 rounded-full">
                        Active
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Token expires: Never (OAuth refresh enabled)
                    </p>
                  </div>
                )}
                {(integrationStatus?.google.gmail.connected || integrationStatus?.google.calendar.connected) && (
                  <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        Google Integration
                      </p>
                      <span className="px-2 py-1 text-xs font-medium bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-400 rounded-full">
                        Active
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                      Gmail: {integrationStatus.google.gmail.connected ? "Connected" : "Not connected"} | Calendar: {integrationStatus.google.calendar.connected ? "Connected" : "Not connected"}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Token expires: Never (OAuth refresh enabled)
                    </p>
                  </div>
                )}
                {(!integrationStatus?.hubspot.connected && !integrationStatus?.google.gmail.connected && !integrationStatus?.google.calendar.connected) && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    No active integrations. <Link href="/integrations" className="text-indigo-600 dark:text-indigo-400 hover:underline">Connect one</Link> to get started.
                  </p>
                )}
              </>
            )}
          </div>
        </SettingsSection>

        {/* Integrations Management */}
        <SettingsSection
          icon={Link2}
          title="Integrations Management"
          description="Quick access to your connected services"
        >
          <div className="space-y-3">
            <Link
              href="/integrations"
              className="block p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-indigo-300 dark:hover:border-indigo-700 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    Manage Integrations
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    View and manage all your connected services
                  </p>
                </div>
                <Link2 className="w-5 h-5 text-gray-400" />
              </div>
            </Link>
          </div>
        </SettingsSection>

        {/* Data & Privacy */}
        <SettingsSection
          icon={Shield}
          title="Data & Privacy"
          description="Control your data and privacy settings"
        >
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                Export Your Data
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                Download all your conversations, integrations, and settings
              </p>
              <button className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors text-sm font-medium flex items-center gap-2">
                <Download className="w-4 h-4" />
                Export Data
              </button>
            </div>
            <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
              <p className="text-sm font-medium text-red-600 dark:text-red-400 mb-2">
                Danger Zone
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                Permanently delete your account and all associated data
              </p>
              <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium flex items-center gap-2">
                <Trash2 className="w-4 h-4" />
                Delete Account
              </button>
            </div>
          </div>
        </SettingsSection>
      </div>
    </div>
  );
}

interface SettingsSectionProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  children: React.ReactNode;
}

function SettingsSection({ icon: Icon, title, description, children }: SettingsSectionProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-start gap-4 mb-6">
        <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/20">
          <Icon className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
        </div>
        <div className="flex-1">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-1">
            {title}
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {description}
          </p>
        </div>
      </div>
      {children}
    </div>
  );
}
