import { currentUser } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

// Force dynamic rendering - this page requires auth
export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const user = await currentUser();

  if (!user) {
    redirect("/sign-in");
  }

  const displayName =
    user.firstName || user.emailAddresses[0]?.emailAddress || "User";

  return (
    <div className="min-h-screen bg-background pt-20">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Welcome, {displayName}
        </h1>
        <p className="text-muted-foreground mb-8">Your RepliMap Dashboard</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-lg border border-border bg-card">
            <h3 className="font-semibold text-foreground mb-2">License</h3>
            <p className="text-2xl font-bold text-emerald-400">Free Tier</p>
            <p className="text-sm text-muted-foreground mt-1">
              3 scans remaining this month
            </p>
          </div>

          <div className="p-6 rounded-lg border border-border bg-card">
            <h3 className="font-semibold text-foreground mb-2">Usage</h3>
            <p className="text-2xl font-bold text-foreground">0 Scans</p>
            <p className="text-sm text-muted-foreground mt-1">
              0 resources analyzed
            </p>
          </div>

          <div className="p-6 rounded-lg border border-border bg-card">
            <h3 className="font-semibold text-foreground mb-2">Quick Start</h3>
            <code className="text-sm text-emerald-400 bg-slate-900 px-3 py-2 rounded block">
              pip install replimap
            </code>
          </div>
        </div>
      </div>
    </div>
  );
}
