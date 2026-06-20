"use client";

import Link from "next/link";
import { useInterviews } from "@/hooks/useInterview";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { EmptyState } from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function InterviewsPage() {
  const { data, isLoading } = useInterviews();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Interviews</h1>
        <Link href="/dashboard/interviews/new">
          <Button>New Interview</Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-muted-foreground">Loading...</div>
      ) : !data?.items?.length ? (
        <EmptyState
          title="No interviews yet"
          description="Create your first interview to get started."
          actionLabel="New Interview"
          onAction={() => window.location.href = "/dashboard/interviews/new"}
        />
      ) : (
        <Card>
          <CardContent className="p-0">
            <table className="w-full">
              <thead>
                <tr className="border-b text-left text-sm text-muted-foreground">
                  <th className="p-3">Interview</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Questions</th>
                  <th className="p-3">Score</th>
                  <th className="p-3">Created</th>
                  <th className="p-3"></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((interview) => (
                  <tr key={interview.id} className="border-b last:border-0 hover:bg-muted/50">
                    <td className="p-3 font-medium">{interview.id.slice(0, 8)}...</td>
                    <td className="p-3"><StatusBadge status={interview.status} /></td>
                    <td className="p-3">{interview.questions_answered}/{interview.question_count}</td>
                    <td className="p-3">{interview.total_score > 0 ? Math.round(interview.total_score) : "—"}</td>
                    <td className="p-3 text-sm text-muted-foreground">
                      {new Date(interview.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-3">
                      <Link href={`/dashboard/interviews/${interview.id}`}>
                        <Button variant="ghost" size="sm">View</Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
