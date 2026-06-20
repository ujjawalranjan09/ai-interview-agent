"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useInterview, useInterviewQuestions, useSubmitAnswer, useRequestFollowup, useCloseInterview, useSubmitAudioAnswer } from "@/hooks/useInterview";
import { useInterviewWS } from "@/hooks/useInterviewWS";
import { QuestionCard } from "@/components/interview/QuestionCard";
import { AnswerInput } from "@/components/interview/AnswerInput";
import { InterviewProgress } from "@/components/interview/InterviewProgress";
import { LiveScoreCard } from "@/components/interview/LiveScoreCard";
import { FollowUpPrompt } from "@/components/interview/FollowUpPrompt";
import { InterviewComplete } from "@/components/interview/InterviewComplete";

export default function LiveInterviewPage() {
  const params = useParams();
  const id = params.id as string;
  const { data: interview } = useInterview(id);
  const { data: questions } = useInterviewQuestions(id);
  const submitAnswer = useSubmitAnswer();
  const submitAudioAnswer = useSubmitAudioAnswer();
  const requestFollowup = useRequestFollowup();
  const closeInterview = useCloseInterview();

  // WebSocket for real-time updates
  const tokens = typeof window !== "undefined" ? sessionStorage.getItem("auth-tokens") : null;
  const authToken = tokens ? JSON.parse(tokens).accessToken : null;
  const { status: wsStatus, lastMessage } = useInterviewWS(id, authToken);

  const [currentIndex, setCurrentIndex] = useState(0);
  const [evaluation, setEvaluation] = useState<Record<string, unknown> | null>(null);
  const [followup, setFollowup] = useState<{ id: string; question_text: string; question_type: string; difficulty: string; order_index: number } | null>(null);
  const [isComplete, setIsComplete] = useState(false);

  // Handle WebSocket messages for real-time updates
  useEffect(() => {
    if (!lastMessage) return;

    switch (lastMessage.type) {
      case "answer_submitted":
        // Handle real-time answer submission from other clients
        console.log("Answer submitted via WebSocket:", lastMessage);
        break;
      case "question_answered":
        // Handle question answered event
        console.log("Question answered via WebSocket:", lastMessage);
        break;
      case "interview_started":
        // Handle interview started event
        console.log("Interview started via WebSocket:", lastMessage);
        break;
      case "interview_paused":
        // Handle interview paused event
        console.log("Interview paused via WebSocket:", lastMessage);
        break;
      case "interview_resumed":
        // Handle interview resumed event
        console.log("Interview resumed via WebSocket:", lastMessage);
        break;
      case "interview_closed":
        // Handle interview closed event
        setIsComplete(true);
        break;
      default:
        break;
    }
  }, [lastMessage, setIsComplete]);

  const mainQuestions = questions?.filter((q) => !q.follow_up_of) || [];
  const currentQuestion = followup || questions?.[currentIndex];

  const handleAnswer = async (answer: string) => {
    if (!currentQuestion) return;
    const result = await submitAnswer.mutateAsync({ questionId: currentQuestion.id, answer_text: answer });
    setEvaluation(result);
  };

  const handleAudioUpload = async (blob: Blob) => {
    if (!currentQuestion) return;
    try {
      const result = await submitAudioAnswer.mutateAsync({ questionId: currentQuestion.id, blob });
      setEvaluation(result);
    } catch {
      // Error is handled by the mutation's onError; evaluation stays null
    }
  };

  const handleNext = async () => {
    setEvaluation(null);
    setFollowup(null);
    if (currentIndex < mainQuestions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      try {
        await closeInterview.mutateAsync(id);
      } catch {
        // Close failed
      }
      setIsComplete(true);
    }
  };

  const handleRequestFollowup = async () => {
    if (!currentQuestion) return;
    const result = await requestFollowup.mutateAsync(currentQuestion.id);
    setFollowup(result);
    setEvaluation(null);
  };

  const handleSkipFollowup = () => {
    setFollowup(null);
    handleNext();
  };

  if (isComplete) {
    return (
      <InterviewComplete
        interviewId={id}
        averageScore={interview?.total_score || 0}
        questionsAnswered={interview?.questions_answered || 0}
      />
    );
  }

  if (!currentQuestion || !mainQuestions.length) {
    return <div className="text-center py-12 text-muted-foreground">Loading interview...</div>;
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <InterviewProgress current={currentIndex + 1} total={mainQuestions.length} />
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${wsStatus === "connected" ? "bg-green-500" : wsStatus === "connecting" ? "bg-yellow-500" : "bg-red-500"}`} />
          <span className="text-xs text-muted-foreground">
            {wsStatus === "connected" ? "Live" : wsStatus === "connecting" ? "Connecting..." : "Offline"}
          </span>
        </div>
      </div>

      {evaluation ? (
        <div className="space-y-4">
          <LiveScoreCard evaluation={evaluation as { total_score: number; semantic_score: number; keyword_score: number; concept_score: number; feedback?: string }} />
          <div className="flex gap-2 justify-center">
            <button onClick={handleRequestFollowup} className="text-sm text-primary hover:underline">
              Request Follow-up
            </button>
            <button onClick={handleNext} className="text-sm text-muted-foreground hover:underline">
              Next Question
            </button>
          </div>
        </div>
      ) : followup ? (
        <>
          <FollowUpPrompt
            questionText={followup.question_text}
            onAnswer={() => {}}
            onSkip={handleSkipFollowup}
          />
          <AnswerInput
            onSubmit={handleAnswer}
            onAudioUpload={handleAudioUpload}
            isLoading={submitAnswer.isPending}
            isUploading={submitAudioAnswer.isPending}
          />
        </>
      ) : (
        <>
          <QuestionCard question={currentQuestion} totalQuestions={mainQuestions.length} />
          <AnswerInput
            onSubmit={handleAnswer}
            onAudioUpload={handleAudioUpload}
            isLoading={submitAnswer.isPending}
            isUploading={submitAudioAnswer.isPending}
          />
        </>
      )}
    </div>
  );
}
