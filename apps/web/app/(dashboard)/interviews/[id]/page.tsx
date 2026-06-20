"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useInterview, useStartInterview, useCloseInterview } from "@/hooks/useInterview";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const TABS = [
  { label: "Overview", href: "" },
  { label: "Results", href: "/results" },
  { label: "Replay", href: "/replay" },
  { label: "Coaching", href: "/coaching" },
];

export default function InterviewDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const { data: interview, isLoading } = useInterview(id);
  const startInterview = useStartInterview();
  const closeInterview = useCloseInterview();

  if (isLoading) return <div className="text-center py-12 text-muted-foreground">Loading...</div>;
  if (!interview) return <div className="text-center py-12 text-muted-foreground">Interview not found</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Interview {interview.id.slice(0, 8)}...</h1>
        <StatusBadge status={interview.status} />
      </div>

      {interview.status === "completed" && (
        <div className="flex gap-1 border-b">
          {TABS.map((tab) => (
            <Link key={tab.label} href={`/dashboard/interviews/${id}${tab.href}`}
              className="pb-2 px-3 text-sm font-medium border-b-2 border-transparent text-muted-foreground hover:text-foreground transition-colors">
              {tab.label}
            </Link>
          ))}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Score</CardTitle></CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{interview.total_score > 0 ? Math.round(interview.total_score) : "—"}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Questions</CardTitle></CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{interview.questions_answered}/{interview.question_count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Difficulty</CardTitle></CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{interview.difficulty_level}</div>
          </CardContent>
        </Card>
      </div>

      <div className="flex gap-2">
        {interview.status === "draft" && (
          <Button onClick={() => startInterview.mutateAsync(id)} disabled={startInterview.isPending}>
            Start Interview
          </Button>
        )}
        {interview.status === "in_progress" && (
          <>
            <Link href={`/dashboard/interviews/${id}/live`}>
              <Button>Open Live View</Button>
            </Link>
            <Button variant="outline" onClick={() => closeInterview.mutateAsync(id)} disabled={closeInterview.isPending}>
              Close Interview
            </Button>
          </>
        )}
        {interview.status === "completed" && (
          <div className="text-sm text-muted-foreground">
            Completed {interview.end_time ? new Date(interview.end_time).toLocaleString() : ""}
          </div>
        )}
      </div>
    </div>
  );
}
