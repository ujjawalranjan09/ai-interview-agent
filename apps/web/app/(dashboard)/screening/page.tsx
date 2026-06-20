"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Brain, Loader2, Download } from "lucide-react";
import { useScreenCandidate, useRankCandidates } from "@/hooks/useScreening";
import { ScreeningResult } from "@/components/screening/ScreeningResult";

export default function ScreeningPage() {
  const [jobDescription, setJobDescription] = useState("");
  const [candidateIds, setCandidateIds] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const screenCandidate = useScreenCandidate();
  const rankCandidates = useRankCandidates();

  const handleScreen = async () => {
    if (!candidateIds.trim()) return;
    const ids = candidateIds.split("\n").map(s => s.trim()).filter(Boolean);
    try {
      const result = await rankCandidates.mutateAsync({ job_description: jobDescription, candidate_ids: ids });
      setResults(result.rankings || result);
      toast.success(`Screened ${ids.length} candidates`);
    } catch {
      toast.error("Screening failed");
    }
  };

  const handleExport = () => {
    if (!results.length) return;
    const csv = "candidate_id,score,recommendation\n" + results.map(r => `${r.candidate_id},${r.score},${r.recommendation}`).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "screening-results.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">AI Resume Screening</h1>
        <p className="text-muted-foreground">Analyze candidates against job descriptions</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Job Description</CardTitle>
          <CardDescription>Paste the job description to screen candidates against</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            placeholder="Paste the job description here (min 50 characters)..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            rows={8}
          />
          <div className="space-y-2">
            <label className="text-sm font-medium">Candidate IDs (one per line)</label>
            <Textarea
              placeholder="candidate-uuid-1&#10;candidate-uuid-2&#10;candidate-uuid-3"
              value={candidateIds}
              onChange={(e) => setCandidateIds(e.target.value)}
              rows={4}
            />
          </div>
          <div className="flex gap-2">
            <Button onClick={handleScreen} disabled={rankCandidates.isPending || jobDescription.length < 50 || !candidateIds.trim()}>
              {rankCandidates.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Brain className="mr-2 h-4 w-4" />}
              Screen Candidates
            </Button>
            {results.length > 0 && (
              <Button variant="outline" onClick={handleExport}>
                <Download className="mr-2 h-4 w-4" /> Export CSV
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {results.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Results ({results.length} candidates)</h2>
          {results.map((r, i) => (
            <ScreeningResult key={r.candidate_id || i} result={r} />
          ))}
        </div>
      )}
    </div>
  );
}
