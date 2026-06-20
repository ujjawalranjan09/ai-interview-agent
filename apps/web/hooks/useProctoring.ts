"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useProctoringSession(interviewId?: string) {
  return useQuery({
    queryKey: ["proctoring", "sessions", interviewId],
    queryFn: () => {
      const params = new URLSearchParams();
      if (interviewId) params.set("interview_id", interviewId);
      return apiFetch(`/api/v1/proctoring/sessions?${params}`);
    },
    enabled: !!interviewId,
  });
}

export function useStartProctoring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { interview_id: string; config?: Record<string, any> }) =>
      apiFetch("/api/v1/proctoring/sessions", { method: "POST", json: data }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["proctoring"] }),
  });
}

export function useEndProctoring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) =>
      apiFetch(`/api/v1/proctoring/sessions/${sessionId}/end`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["proctoring"] }),
  });
}

export function useLogProctoringEvent() {
  return useMutation({
    mutationFn: ({ sessionId, ...data }: { sessionId: string; event_type: string; severity?: string; confidence?: number; details?: Record<string, any> }) =>
      apiFetch(`/api/v1/proctoring/sessions/${sessionId}/events`, { method: "POST", json: data }),
  });
}
