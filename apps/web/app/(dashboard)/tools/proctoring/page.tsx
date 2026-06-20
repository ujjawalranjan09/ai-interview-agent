"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { Shield, ShieldAlert, ShieldCheck, Loader2, Eye } from "lucide-react";
import { useProctoringSession, useStartProctoring, useEndProctoring } from "@/hooks/useProctoring";

export default function ProctoringPage() {
  const [interviewId, setInterviewId] = useState("");
  const [sessionId, setSessionId] = useState("");
  const { data: sessions, isLoading } = useProctoringSession(interviewId || undefined);
  const startProctoring = useStartProctoring();
  const endProctoring = useEndProctoring();

  const handleStart = async () => {
    if (!interviewId) return;
    try {
      const result = await startProctoring.mutateAsync({ interview_id: interviewId });
      setSessionId(result.id);
      toast.success("Proctoring session started");
    } catch {
      toast.error("Failed to start proctoring");
    }
  };

  const handleEnd = async () => {
    if (!sessionId) return;
    try {
      await endProctoring.mutateAsync(sessionId);
      toast.success("Proctoring session ended");
    } catch {
      toast.error("Failed to end proctoring");
    }
  };

  const riskIcon = (score: number) => {
    if (score < 0.3) return <ShieldCheck className="h-4 w-4 text-green-500" />;
    if (score < 0.7) return <ShieldAlert className="h-4 w-4 text-yellow-500" />;
    return <Shield className="h-4 w-4 text-red-500" />;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">AI Proctoring</h1>
        <p className="text-muted-foreground">Monitor and manage proctoring sessions</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Manage Session</CardTitle>
          <CardDescription>Start or end a proctoring session for an interview</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Interview ID"
              value={interviewId}
              onChange={(e) => setInterviewId(e.target.value)}
            />
            <Button onClick={handleStart} disabled={startProctoring.isPending || !interviewId}>
              {startProctoring.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Eye className="mr-2 h-4 w-4" />
              )}
              Start
            </Button>
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="Session ID (to end)"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
            />
            <Button variant="destructive" onClick={handleEnd} disabled={endProctoring.isPending || !sessionId}>
              End Session
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent Sessions</CardTitle>
          <CardDescription>Proctoring sessions for the selected interview</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : sessions?.items?.length ? (
            <div className="space-y-3">
              {sessions.items.map((s: any) => (
                <div key={s.id} className="flex items-center justify-between rounded-lg border p-3">
                  <div className="flex items-center gap-3">
                    {riskIcon(s.risk_score)}
                    <div>
                      <p className="text-sm font-medium">
                        Session {s.id.slice(0, 8)}...
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Started: {new Date(s.started_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm">{s.flags_total} flags</p>
                    <p className="text-xs text-muted-foreground">Risk: {(s.risk_score * 100).toFixed(0)}%</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No proctoring sessions yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
