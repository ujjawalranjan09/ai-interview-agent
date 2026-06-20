"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCreateInterview, useStartInterview } from "@/hooks/useInterview";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { apiFetch } from "@/lib/api";

export default function NewInterviewPage() {
  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");
  const [questionCount, setQuestionCount] = useState(10);
  const [difficulty, setDifficulty] = useState(2);
  const [generateShareLink, setGenerateShareLink] = useState(false);
  const [shareUrl, setShareUrl] = useState("");
  const createInterview = useCreateInterview();
  const startInterview = useStartInterview();
  const router = useRouter();

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Create candidate first
      const candidate = await apiFetch<{ id: string }>("/api/v1/candidates", {
        method: "POST",
        json: { name: candidateName, email: candidateEmail },
      });

      // Create interview
      const interview = await createInterview.mutateAsync({
        candidate_id: candidate.id,
        question_count: questionCount,
        difficulty_level: difficulty,
      });

      // Start interview
      const started = await startInterview.mutateAsync(interview.id);

      // Generate share link if requested
      if (generateShareLink) {
        const shareResult = await apiFetch<{ share_token: string; share_url: string }>(
          `/api/v1/interviews/${started.id}/share`,
          { method: "POST" }
        );
        setShareUrl(shareResult.share_url);
        toast.success("Share link generated!");
      } else {
        toast.success("Interview started!");
        router.push(`/dashboard/interviews/${started.id}/live`);
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to create interview");
    }
  };

  const copyShareLink = () => {
    navigator.clipboard.writeText(shareUrl);
    toast.success("Link copied!");
  };

  if (shareUrl) {
    return (
      <div className="max-w-lg mx-auto space-y-6">
        <h1 className="text-2xl font-bold">Interview Created</h1>
        <Card>
          <CardHeader>
            <CardTitle>Share Link</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Share this link with the candidate. They can answer questions without logging in.
            </p>
            <div className="flex gap-2">
              <Input value={shareUrl} readOnly />
              <Button onClick={copyShareLink}>Copy</Button>
            </div>
            <Button
              variant="outline"
              className="w-full"
              onClick={() => router.push("/dashboard/interviews")}
            >
              Back to Interviews
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <h1 className="text-2xl font-bold">New Interview</h1>
      <Card>
        <CardHeader>
          <CardTitle>Candidate Information</CardTitle>
        </CardHeader>
        <form onSubmit={handleCreate}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Candidate Name</Label>
              <Input id="name" value={candidateName} onChange={(e) => setCandidateName(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={candidateEmail} onChange={(e) => setCandidateEmail(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="count">Number of Questions</Label>
              <Input id="count" type="number" min={3} max={20} value={questionCount} onChange={(e) => setQuestionCount(Number(e.target.value))} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="difficulty">Difficulty (1-4)</Label>
              <Input id="difficulty" type="number" min={1} max={4} value={difficulty} onChange={(e) => setDifficulty(Number(e.target.value))} />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="share-link"
                checked={generateShareLink}
                onChange={(e) => setGenerateShareLink(e.target.checked)}
              />
              <Label htmlFor="share-link">Generate shareable link for candidate</Label>
            </div>
            <Button type="submit" className="w-full" disabled={createInterview.isPending || startInterview.isPending}>
              {createInterview.isPending || startInterview.isPending ? "Creating..." : "Create & Start Interview"}
            </Button>
          </CardContent>
        </form>
      </Card>
    </div>
  );
}
