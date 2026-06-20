"use client";

import { useParams } from "next/navigation";
import { useInterviewReport } from "@/hooks/usePortal";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function PortalInterviewDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: report, isLoading } = useInterviewReport(id);

  if (isLoading) {
    return <div className="text-center py-12 text-muted-foreground">Loading...</div>;
  }

  if (!report) {
    return <div className="text-center py-12 text-muted-foreground">Interview not found</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Interview Report</h1>
        <Link href="/portal/interviews">
          <Button variant="ghost">← Back to Interviews</Button>
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Overall Score</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <div className={`text-5xl font-bold ${
              (report.total_score || 0) >= 70
                ? "text-green-600"
                : (report.total_score || 0) >= 50
                ? "text-yellow-600"
                : "text-red-600"
            }`}>
              {report.total_score ? Math.round(report.total_score) : "—"}
            </div>
            <p className="text-muted-foreground mt-2">out of 100</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Questions</CardTitle>
          </CardHeader>
          <CardContent>
            <p><span className="font-medium">Answered:</span> {report.questions_answered}</p>
            <p><span className="font-medium">Total:</span> {report.question_count}</p>
            <p><span className="font-medium">Status:</span> {report.status}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Timing</CardTitle>
          </CardHeader>
          <CardContent>
            <p>
              <span className="font-medium">Started:</span>{" "}
              {report.start_time ? new Date(report.start_time).toLocaleString() : "—"}
            </p>
            <p>
              <span className="font-medium">Ended:</span>{" "}
              {report.end_time ? new Date(report.end_time).toLocaleString() : "—"}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Question Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {report.questions.map((q, i) => (
            <div key={q.id} className="border rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="font-medium">Q{i + 1}: {q.question_text}</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Type: {q.question_type} • Difficulty: {q.difficulty}
                  </p>
                </div>
                <div className={`text-lg font-bold ${
                  (q.score || 0) >= 70
                    ? "text-green-600"
                    : (q.score || 0) >= 50
                    ? "text-yellow-600"
                    : "text-red-600"
                }`}>
                  {q.score ? Math.round(q.score) : "—"}
                </div>
              </div>
              {q.answer && (
                <div className="mt-3">
                  <p className="text-sm font-medium">Your Answer:</p>
                  <p className="text-sm bg-muted p-2 rounded mt-1">{q.answer}</p>
                </div>
              )}
              <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
                <span>Semantic: {q.semantic_score ? Math.round(q.semantic_score) : "—"}</span>
                <span>Keywords: {q.keyword_score ? Math.round(q.keyword_score) : "—"}</span>
                <span>Concepts: {q.concept_score ? Math.round(q.concept_score) : "—"}</span>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
