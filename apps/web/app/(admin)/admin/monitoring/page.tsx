"use client";
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Activity, Database, Clock, AlertTriangle } from "lucide-react";
import { apiFetch } from "@/lib/api";

interface HealthStatus {
  status: string;
  timestamp: string;
  checks?: Record<string, string>;
}

export default function MonitoringPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [ready, setReady] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const check = async () => {
      try {
        const [h, r] = await Promise.all([
          apiFetch("/api/v1/health") as Promise<HealthStatus>,
          apiFetch("/api/v1/health/ready") as Promise<HealthStatus>,
        ]);
        setHealth(h);
        setReady(r);
      } catch {
        setHealth({ status: "unreachable", timestamp: new Date().toISOString() });
      }
      setLoading(false);
    };
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="flex items-center justify-center p-8"><Loader2 className="h-6 w-6 animate-spin" /></div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Monitoring</h1>
        <p className="text-muted-foreground">System health and performance metrics</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Activity className="h-4 w-4 text-green-500" />
              Service Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={health?.status === "ok" ? "default" : "destructive"}>
              {health?.status || "unknown"}
            </Badge>
            <p className="mt-2 text-xs text-muted-foreground">
              Last checked: {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : "never"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Database className="h-4 w-4 text-blue-500" />
              Database Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            {ready?.checks ? (
              Object.entries(ready.checks).map(([key, val]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-sm capitalize">{key}</span>
                  <Badge variant={val === "ok" ? "default" : "destructive"}>{val}</Badge>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">Not available</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Clock className="h-4 w-4 text-orange-500" />
              Uptime Checks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Auto-refreshes every 30s &middot; Metrics available at <code className="font-mono bg-muted px-1 rounded">/metrics</code>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
