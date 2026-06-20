"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useReplayData } from "@/hooks/useReport";

interface ReplayData {
  events: { type: string; timestamp: number; data: Record<string, unknown> }[];
  total_duration: number;
  emotion_markers: { time: number; emotion: string; confidence: number }[];
  score_progression: { order: number; score: number; type: string; difficulty: string }[];
}

export default function ReplayPage() {
  const params = useParams();
  const id = params.id as string;
  const { data: replay, isLoading } = useReplayData(id) as { data: ReplayData | undefined; isLoading: boolean };
  const [position, setPosition] = useState(0);

  if (isLoading) return <div className="text-center py-12 text-muted-foreground">Loading replay...</div>;
  if (!replay) return <div className="text-center py-12 text-muted-foreground">No replay data available</div>;

  const events = replay.events || [];
  const totalDuration = Math.max(replay.total_duration || 1, 1);
  const safePosition = Math.min(Math.max(position, 0), totalDuration);
  const currentEvents = events.filter((e: { timestamp: number }) => e.timestamp <= safePosition);
  const currentQuestion = [...currentEvents].reverse().find((e: { type: string }) => e.type === "question");
  const currentEmotion = [...currentEvents].reverse().find((e: { type: string }) => e.type === "emotion");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Interview Replay</h1>

      <div className="space-y-2">
        <input
          type="range" min={0} max={totalDuration} step={0.1}
          value={safePosition} onChange={(e) => setPosition(Number(e.target.value))}
          className="w-full"
        />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{Math.floor(safePosition)}s</span>
          <span>{Math.floor(totalDuration)}s</span>
        </div>
      </div>

      {currentEmotion && (
        <div className="p-4 rounded-lg bg-muted/50 flex items-center gap-4">
          <span className="text-2xl">
            {(currentEmotion.data as Record<string, unknown>)?.emotion === "confident" ? "😊" :
             (currentEmotion.data as Record<string, unknown>)?.emotion === "nervous" ? "😰" :
             (currentEmotion.data as Record<string, unknown>)?.emotion === "excited" ? "🤩" : "😐"}
          </span>
          <div>
            <p className="font-medium capitalize">{String((currentEmotion.data as Record<string, unknown>)?.emotion || "neutral")}</p>
            <p className="text-sm text-muted-foreground">Confidence: {Math.round(Number((currentEmotion.data as Record<string, unknown>)?.confidence) || 50)}%</p>
          </div>
        </div>
      )}

      {currentQuestion && (
        <div className="border rounded-lg p-4 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary">{String((currentQuestion.data as Record<string, unknown>)?.question_type || "")}</span>
            <span className="text-xs text-muted-foreground">Q{Number((currentQuestion.data as Record<string, unknown>)?.order || 0) + 1}</span>
          </div>
          <p className="font-medium">{String((currentQuestion.data as Record<string, unknown>)?.question_text || "")}</p>
          {Boolean((currentQuestion.data as Record<string, unknown>)?.answer_text) && (
            <p className="text-sm text-muted-foreground">{String((currentQuestion.data as Record<string, unknown>)?.answer_text)}</p>
          )}
          {Number((currentQuestion.data as Record<string, unknown>)?.answer_score || 0) > 0 && (
            <span className={`text-sm font-bold ${Number((currentQuestion.data as Record<string, unknown>)?.answer_score || 0) >= 80 ? "text-green-600" : "text-yellow-600"}`}>
              Score: {Math.round(Number((currentQuestion.data as Record<string, unknown>)?.answer_score || 0))}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
