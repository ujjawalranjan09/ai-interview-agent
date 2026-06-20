"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { Search, AlertTriangle, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { useCreatePlagiarismCheck, useRunAnalysis, usePlagiarismCheck } from "@/hooks/usePlagiarism";

export default function PlagiarismPage() {
  const [submissionId, setSubmissionId] = useState("");
  const [checkId, setCheckId] = useState("");
  const createCheck = useCreatePlagiarismCheck();
  const runAnalysis = useRunAnalysis();
  const { data: checkResult, isLoading: checkLoading } = usePlagiarismCheck(checkId || undefined);

  const handleCreate = async () => {
    if (!submissionId) return;
    try {
      const result = await createCheck.mutateAsync(submissionId);
      setCheckId(result.id);
      toast.success("Plagiarism check created");
    } catch {
      toast.error("Failed to create check");
    }
  };

  const handleAnalyze = async () => {
    if (!checkId) return;
    try {
      const result = await runAnalysis.mutateAsync(checkId);
      toast.success(`Analysis complete: ${(result.similarity_score * 100).toFixed(1)}% similarity`);
    } catch {
      toast.error("Analysis failed");
    }
  };

  const similarityColor = (score: number | null | undefined) => {
    if (score == null) return "text-muted-foreground";
    if (score < 0.3) return "text-green-500";
    if (score < 0.7) return "text-yellow-500";
    return "text-red-500";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Plagiarism Detection</h1>
        <p className="text-muted-foreground">Analyze coding submissions for similarity</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>New Check</CardTitle>
          <CardDescription>Enter a submission ID to check for plagiarism</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Submission ID"
              value={submissionId}
              onChange={(e) => setSubmissionId(e.target.value)}
            />
            <Button onClick={handleCreate} disabled={createCheck.isPending || !submissionId}>
              {createCheck.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Search className="mr-2 h-4 w-4" />
              )}
              Create Check
            </Button>
          </div>
          {checkId && (
            <div className="flex items-center gap-2">
              <Input value={checkId} readOnly placeholder="Check ID" />
              <Button variant="default" onClick={handleAnalyze} disabled={runAnalysis.isPending}>
                {runAnalysis.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <AlertTriangle className="mr-2 h-4 w-4" />
                )}
                Run Analysis
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {checkResult && (
        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
            <CardDescription>Plagiarism check results</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Status</span>
              <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                checkResult.status === "completed" ? "bg-green-100 text-green-800" :
                checkResult.status === "pending" ? "bg-yellow-100 text-yellow-800" :
                "bg-red-100 text-red-800"
              }`}>
                {checkResult.status === "completed" ? <CheckCircle2 className="h-3 w-3" /> :
                 checkResult.status === "failed" ? <XCircle className="h-3 w-3" /> : null}
                {checkResult.status}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Overall Similarity</span>
              <span className={`text-lg font-bold ${similarityColor(checkResult.similarity_score)}`}>
                {checkResult.similarity_score != null
                  ? `${(checkResult.similarity_score * 100).toFixed(1)}%`
                  : "N/A"}
              </span>
            </div>
            {checkResult.matches?.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">Matches ({checkResult.matches.length})</p>
                <div className="space-y-2">
                  {checkResult.matches.map((m: any) => (
                    <div key={m.id} className="flex items-center justify-between rounded border p-2 text-sm">
                      <span className="text-muted-foreground">
                        Submission {m.matched_submission_id.slice(0, 8)}...
                      </span>
                      <span className={`font-medium ${similarityColor(m.similarity)}`}>
                        {(m.similarity * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
