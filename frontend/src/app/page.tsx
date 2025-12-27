import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-4">BridgeAI</h1>
        <p className="text-muted-foreground mb-8">AI Integration Copilot</p>
        <div className="flex gap-4">
          <Link
            href="/integrations"
            className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Manage Integrations
          </Link>
        </div>
      </div>
    </main>
  );
}

