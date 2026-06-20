"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type PageState = "loading" | "welcome" | "active" | "complete";

interface InterviewInfo {
  id: string;
  candidate_name: string;
  question_count: number;
  difficulty_level: string;
  status: string;
  first_question: NextQuestion | null;
}

interface NextQuestion {
  id: string;
  question_text: string;
  question_type: string;
  difficulty: string;
  order_index: number;
}

export default function JoinInterviewPage() {
  const { token } = useParams<{ token: string }>();
  const [state, setState] = useState<PageState>("loading");
  const [info, setInfo] = useState<InterviewInfo | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<NextQuestion | null>(null);
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/interviews/join/${token}`);
        if (!res.ok) throw new Error("Not found");
        const data = await res.json();
        setInfo(data);
        setState("welcome");
      } catch {
        toast.error("Interview not found or unavailable");
        setState("complete");
      }
    })();
  }, [token]);

  const handleBegin = async () => {
    if (!info) return;
    if (info.first_question) {
      setCurrentQuestion(info.first_question as NextQuestion);
      setState("active");
    } else {
      toast.error("No questions available for this interview");
    }
  };

  const handleSubmit = async () => {
    if (!currentQuestion || !answer.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/interviews/join/${token}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question_id: currentQuestion.id, answer_text: answer }),
      });
      const result = await res.json();
      if (result.completed) {
        toast.success(`Interview complete! Score: ${Math.round(result.score)}`);
        setState("complete");
      } else if (result.next_question) {
        toast.success(`Score: ${Math.round(result.score)}`);
        setCurrentQuestion(result.next_question);
        setAnswer("");
      }
    } catch {
      toast.error("Failed to submit answer");
    } finally {
      setSubmitting(false);
    }
  };

  if (state === "loading") {
    return <div className="text-center py-12 text-muted-foreground">Loading interview...</div>;
  }

  if (state === "complete") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Interview Complete</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Thank you for completing the interview. Your responses have been recorded.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (state === "welcome" && info) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Welcome, {info.candidate_name}!</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm space-y-2">
            <p>Questions: <strong>{info.question_count}</strong></p>
            <p>Difficulty: <strong>{info.difficulty_level}</strong></p>
            <p>Status: <strong>{info.status}</strong></p>
          </div>
          <Button className="w-full" onClick={handleBegin}>
            Begin Interview
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (state === "active" && currentQuestion) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Question {currentQuestion.order_index + 1}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="font-medium">{currentQuestion.question_text}</p>
          <textarea
            className="w-full rounded-md border p-2 min-h-[150px]"
            placeholder="Type your answer..."
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
          />
          <Button
            className="w-full"
            onClick={handleSubmit}
            disabled={submitting || !answer.trim()}
          >
            {submitting ? "Submitting..." : "Submit Answer"}
          </Button>
        </CardContent>
      </Card>
    );
  }

  return null;
}
