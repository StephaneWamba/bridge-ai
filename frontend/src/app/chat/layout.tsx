// Chat page uses DashboardLayout as wrapper, with ChatLayout for conversation-specific UI
// ChatLayout has its own header with top navigation, so we hide the dashboard header
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";

export default function ChatLayoutWrapper({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <DashboardLayout hideHeader={true}>{children}</DashboardLayout>
    </ProtectedRoute>
  );
}

