// Chat page uses its own layout (ChatLayout) instead of DashboardLayout
// This allows the conversation sidebar to work properly
export default function ChatLayoutWrapper({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}

