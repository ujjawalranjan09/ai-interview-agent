"use client";

import { useSystemHealth, useSystemStats } from "@/hooks/useAdmin";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AdminSystemPage() {
  const { data: health } = useSystemHealth();
  const { data: stats, isLoading } = useSystemStats();

  if (isLoading) {
    return <div className="text-center py-12 text-muted-foreground">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">System Health</h1>

      <Card>
        <CardHeader>
          <CardTitle>Health Status</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center gap-4">
          <span
            className={`h-4 w-4 rounded-full ${
              health?.status === "healthy" ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <div>
            <p className="font-medium">
              Database:{" "}
              <span
                className={
                  health?.database === "connected" ? "text-green-600" : "text-red-600"
                }
              >
                {health?.database || "unknown"}
              </span>
            </p>
            <p className="text-sm text-muted-foreground">
              Last checked: {health?.timestamp ? new Date(health.timestamp).toLocaleString() : "—"}
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Users
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_users || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Interviews
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_interviews || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Candidates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_candidates || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Sessions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.active_sessions || 0}</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
