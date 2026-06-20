"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useInterviews } from "@/hooks/useInterview";
import { useStartCopilot } from "@/hooks/useCopilot";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function CopilotSetupPage() {
  const { data, isLoading } = useInterviews({ status: "in_progress" });
  const [selectedId, setSelectedId] = useState("");
  const startCopilot = useStartCopilot(selectedId);
  const router = useRouter();

  const activeInterviews = data?.items || [];

  const handleStart = async () => {
    if (!selectedId) return;
    await startCopilot.mutateAsync();
    router.push(`/copilot/${selectedId}`);
  };

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Copilot Mode</h1>
      <Card>
        <CardHeader>
          <CardTitle>Select Active Interview</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <p className="text-muted-foreground">Loading interviews...</p>
          ) : activeInterviews.length === 0 ? (
            <p className="text-muted-foreground">No active interviews</p>
          ) : (
            <select
              className="w-full rounded-md border p-2"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
            >
              <option value="">Select an interview...</option>
              {activeInterviews.map((iv) => (
                <option key={iv.id} value={iv.id}>
                  {iv.id.slice(0, 8)}... - {iv.candidate_id.slice(0, 8)}...
                </option>
              ))}
            </select>
          )}
          <Button
            className="w-full"
            disabled={!selectedId || startCopilot.isPending}
            onClick={handleStart}
          >
            {startCopilot.isPending ? "Starting..." : "Start Copilot Session"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
