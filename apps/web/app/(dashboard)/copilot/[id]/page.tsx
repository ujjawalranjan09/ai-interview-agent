"use client";

import { useParams } from "next/navigation";
import { useInterview, useInterviewQuestions } from "@/hooks/useInterview";
import {
  useCopilotSuggestions,
  useDismissSuggestion,
} from "@/hooks/useCopilot";
import { useCopilotWS } from "@/hooks/useCopilotWS";
import { CopilotSidebar } from "@/components/copilot/CopilotSidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ActiveCopilotPage() {
  const { id } = useParams<{ id: string }>();
  const { isLoading: ivLoading } = useInterview(id);
  const { data: questions } = useInterviewQuestions(id);
  const { data: suggestionsData } = useCopilotSuggestions(id, true);
  const dismissSuggestion = useDismissSuggestion(id);

  // WebSocket for real-time copilot updates
  const tokens = typeof window !== "undefined" ? sessionStorage.getItem("auth-tokens") : null;
  const authToken = tokens ? JSON.parse(tokens).accessToken : null;
  const {
    status: wsStatus,
    suggestions: wsSuggestions,
    isLoadingSuggestions,
    requestSuggestions,
    dismissSuggestion: wsDismissSuggestion,
  } = useCopilotWS(id, authToken);

  // Use WebSocket suggestions if available, otherwise fall back to API
  const activeSuggestions = wsSuggestions.length > 0
    ? wsSuggestions.map((s) => ({
        id: s.id,
        type: s.category,
        icon: "lightbulb",
        color: "yellow",
        text: s.text,
      }))
    : suggestionsData?.suggestions || [];

  if (ivLoading) {
    return <div className="text-center py-12 text-muted-foreground">Loading...</div>;
  }

  const latestQ = questions?.length ? questions[questions.length - 1] : null;

  const handleDismiss = async (suggestionId: string) => {
    // Try WebSocket first, fall back to API
    if (wsStatus === "connected") {
      wsDismissSuggestion(suggestionId);
    } else {
      await dismissSuggestion.mutateAsync(suggestionId);
    }
  };

  return (
    <div className="flex gap-6 h-full">
      <div className="flex-1 space-y-6">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Copilot &gt; Interview {id.slice(0, 8)}...
          </p>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${wsStatus === "connected" ? "bg-green-500" : wsStatus === "connecting" ? "bg-yellow-500" : "bg-red-500"}`} />
            <span className="text-xs text-muted-foreground">
              {wsStatus === "connected" ? "Live" : wsStatus === "connecting" ? "Connecting..." : "Offline"}
            </span>
          </div>
        </div>
        <h1 className="text-2xl font-bold">Copilot Session</h1>
        {latestQ ? (
          <Card>
            <CardHeader>
              <CardTitle>Current Question</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm font-medium">{latestQ.question_text}</p>
              {latestQ.candidate_answer_text && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">
                    Candidate Answer:
                  </p>
                  <p className="text-sm bg-muted p-2 rounded">
                    {latestQ.candidate_answer_text}
                  </p>
                </div>
              )}
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Score:</span>
                <span
                  className={`text-lg font-bold ${
                    latestQ.answer_score >= 70
                      ? "text-green-600"
                      : latestQ.answer_score >= 50
                      ? "text-yellow-600"
                      : "text-red-600"
                  }`}
                >
                  {Math.round(latestQ.answer_score)}
                </span>
              </div>
            </CardContent>
          </Card>
        ) : (
          <p className="text-muted-foreground">No questions yet</p>
        )}
        <button
          onClick={requestSuggestions}
          disabled={wsStatus !== "connected" || isLoadingSuggestions}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm disabled:opacity-50"
        >
          {isLoadingSuggestions ? "Generating..." : "Get Real-time Suggestions"}
        </button>
      </div>
      <div className="w-80 border-l pl-6">
        <CopilotSidebar
          suggestions={activeSuggestions}
          onDismiss={handleDismiss}
        />
      </div>
    </div>
  );
}
