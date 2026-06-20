"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface InterviewCompleteProps {
  interviewId: string;
  averageScore: number;
  questionsAnswered: number;
}

export function InterviewComplete({ interviewId, averageScore, questionsAnswered }: InterviewCompleteProps) {
  return (
    <Card className="w-full max-w-md mx-auto">
      <CardContent className="pt-6 text-center space-y-4">
        <div className="text-6xl">🎉</div>
        <h2 className="text-2xl font-bold">Interview Complete!</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-3xl font-bold text-primary">{Math.round(averageScore)}</div>
            <div className="text-sm text-muted-foreground">Average Score</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-primary">{questionsAnswered}</div>
            <div className="text-sm text-muted-foreground">Questions Answered</div>
          </div>
        </div>
        <div className="flex gap-2 justify-center pt-4">
          <Link href={`/dashboard/interviews/${interviewId}`}>
            <Button>View Results</Button>
          </Link>
          <Link href="/dashboard/interviews">
            <Button variant="outline">Back to Interviews</Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
