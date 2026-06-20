"use client";

import { useState } from "react";
import { useJdMatch, useJdQuestions } from "@/hooks/useJD";
import { MatchResults } from "@/components/jd/MatchResults";
import { GeneratedQuestions } from "@/components/jd/GeneratedQuestions";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function JDMatchPage() {
  const [jdText, setJdText] = useState("");
  const [candidateId, setCandidateId] = useState("");
  const [matchResult, setMatchResult] = useState<Record<string, unknown> | null>(null);
  const [questions, setQuestions] = useState<Record<string, unknown> | null>(null);

  const matchMutation = useJdMatch(candidateId);
  const questionsMutation = useJdQuestions(candidateId);

  const handleAnalyze = async () => {
    if (!candidateId || jdText.length < 50) return;
    try {
      const result = await matchMutation.mutateAsync({ jd_text: jdText });
      setMatchResult(result as Record<string, unknown>);
      setQuestions(null);
    } catch {
      toast.error("Failed to analyze JD");
    }
  };

  const handleGenerate = async () => {
    if (!candidateId || jdText.length < 50) return;
    try {
      const result = await questionsMutation.mutateAsync({ jd_text: jdText });
      setQuestions(result as Record<string, unknown>);
      setMatchResult(null);
    } catch {
      toast.error("Failed to generate questions");
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Job Description Match</h1>

      <Card>
        <CardHeader>
          <CardTitle>Input</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Candidate ID</label>
            <input
              className="w-full rounded-md border p-2 mt-1"
              placeholder="Paste candidate ID..."
              value={candidateId}
              onChange={(e) => setCandidateId(e.target.value)}
            />
          </div>
          <div>
            <label className="text-sm font-medium">
              Job Description ({jdText.length} chars, min 50)
            </label>
            <textarea
              className="w-full rounded-md border p-2 mt-1 min-h-[200px]"
              placeholder="Paste job description text..."
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
            />
          </div>
          <div className="flex gap-3">
            <Button
              onClick={handleAnalyze}
              disabled={matchMutation.isPending || jdText.length < 50 || !candidateId}
            >
              {matchMutation.isPending ? "Analyzing..." : "Analyze Match"}
            </Button>
            <Button
              variant="outline"
              onClick={handleGenerate}
              disabled={questionsMutation.isPending || jdText.length < 50 || !candidateId}
            >
              {questionsMutation.isPending ? "Generating..." : "Generate Questions"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {matchResult && (
        <Card>
          <CardHeader>
            <CardTitle>Match Results</CardTitle>
          </CardHeader>
          <CardContent>
            <MatchResults
              matchPercentage={matchResult.match_percentage as number}
              matchedRequired={matchResult.matched_required as string[]}
              missingRequired={matchResult.missing_required as string[]}
              matchedPreferred={matchResult.matched_preferred as string[]}
              missingPreferred={matchResult.missing_preferred as string[]}
            />
          </CardContent>
        </Card>
      )}

      {questions && (
        <Card>
          <CardHeader>
            <CardTitle>Generated Questions</CardTitle>
          </CardHeader>
          <CardContent>
            <GeneratedQuestions questions={questions.questions as { question_text: string; question_type: string; difficulty: string; target_skill: string }[]} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
