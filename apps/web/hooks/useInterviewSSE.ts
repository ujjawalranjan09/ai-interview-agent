"use client";

import { useEffect, useRef, useState } from "react";

type SSEStatus = "connecting" | "connected" | "disconnected";

export function useInterviewSSE(interviewId: string, token: string | null) {
  const [status, setStatus] = useState<SSEStatus>("disconnected");
  const [lastEvent, setLastEvent] = useState<{ type: string; data: unknown } | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!interviewId || !token) return;

    const url = `/api/v1/interviews/${interviewId}/events?token=${token}`;

    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.addEventListener("connected", () => setStatus("connected"));
    es.addEventListener("question_asked", (e) => setLastEvent({ type: "question_asked", data: JSON.parse(e.data) }));
    es.addEventListener("answer_evaluated", (e) => setLastEvent({ type: "answer_evaluated", data: JSON.parse(e.data) }));
    es.addEventListener("difficulty_changed", (e) => setLastEvent({ type: "difficulty_changed", data: JSON.parse(e.data) }));
    es.addEventListener("interview_completed", (e) => setLastEvent({ type: "interview_completed", data: JSON.parse(e.data) }));
    es.addEventListener("error", () => setStatus("disconnected"));

    es.onerror = () => {
      setStatus("disconnected");
      es.close();
    };

    return () => {
      es.close();
      setStatus("disconnected");
    };
  }, [interviewId, token]);

  return { status, lastEvent };
}
