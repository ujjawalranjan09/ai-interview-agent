"use client";

import Link from "next/link";
import { useCandidateInterviews } from "@/hooks/usePortal";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function PortalInterviewsPage() {
  const { data, isLoading } = useCandidateInterviews();

  if (isLoading) {
    return <div className="text-center py-12 text-muted-foreground">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">My Interviews</h1>

      {!data?.items?.length ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No interviews yet. You will see your interview history here once you complete an interview.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {data.items.map((interview) => (
            <Card key={interview.id}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Interview {interview.id.slice(0, 8)}...</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(interview.created_at).toLocaleDateString()} •{" "}
                      {interview.questions_answered}/{interview.question_count} questions
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className={`font-medium ${
                        (interview.total_score || 0) >= 70
                          ? "text-green-600"
                          : (interview.total_score || 0) >= 50
                          ? "text-yellow-600"
                          : "text-red-600"
                      }`}>
                        {interview.total_score ? `${Math.round(interview.total_score)}%` : "—"}
                      </p>
                      <p className="text-xs text-muted-foreground">{interview.status}</p>
                    </div>
                    <Link href={`/portal/interviews/${interview.id}`}>
                      <Button variant="outline" size="sm">View Report</Button>
                    </Link>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
