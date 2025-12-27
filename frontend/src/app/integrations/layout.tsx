import { DashboardLayout } from "@/components/dashboard/DashboardLayout";

export default function IntegrationsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <DashboardLayout title="Integrations">{children}</DashboardLayout>;
}

