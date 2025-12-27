"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { fetchAPI } from "@/lib/api/client";

interface IntegrationStatus {
  connected: boolean;
  is_active?: boolean;
  expires_at?: string;
  working?: boolean;
}

function IntegrationsContent() {
  const searchParams = useSearchParams();
  const [hubspotStatus, setHubspotStatus] = useState<IntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const status = await fetchAPI<IntegrationStatus>(
        "/api/v1/integrations/hubspot/status"
      );
      setHubspotStatus(status);
    } catch (error) {
      console.error("Failed to load integration status:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    setConnecting(true);
    try {
      const response = await fetchAPI<{ authorization_url: string }>(
        "/api/v1/integrations/hubspot/authorize"
      );
      window.location.href = response.authorization_url;
    } catch (error) {
      console.error("Failed to initiate OAuth:", error);
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await fetchAPI("/api/v1/integrations/hubspot/disconnect", {
        method: "POST",
      });
      await loadStatus();
    } catch (error) {
      console.error("Failed to disconnect:", error);
    }
  };

  const success = searchParams?.get("success");
  const error = searchParams?.get("error");

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-8">Integrations</h1>

      {success && (
        <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
          Successfully connected to {success}!
        </div>
      )}

      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          Error: {error}
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold">HubSpot</h2>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              Connect your HubSpot CRM to access contacts, companies, and deals
            </p>
          </div>
          <div className="flex items-center gap-2">
            {hubspotStatus?.connected ? (
              <>
                <span
                  className={`px-3 py-1 rounded-full text-sm ${
                    hubspotStatus.working
                      ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                      : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                  }`}
                >
                  {hubspotStatus.working ? "Connected" : "Disconnected"}
                </span>
                <button
                  onClick={handleDisconnect}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Disconnect
                </button>
              </>
            ) : (
              <button
                onClick={handleConnect}
                disabled={connecting}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {connecting ? "Connecting..." : "Connect"}
              </button>
            )}
          </div>
        </div>

        {hubspotStatus?.connected && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">Status:</span>
                <span className="ml-2 font-medium">
                  {hubspotStatus.is_active ? "Active" : "Inactive"}
                </span>
              </div>
              {hubspotStatus.expires_at && (
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Expires:</span>
                  <span className="ml-2 font-medium">
                    {new Date(hubspotStatus.expires_at).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function IntegrationsPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    }>
      <IntegrationsContent />
    </Suspense>
  );
}

