"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useStartCopilot(interviewId: string) {
  return useMutation({
    mutationFn: () =>
      apiFetch(`/api/v1/interviews/${interviewId}/copilot/start`, {
        method: "POST",
      }),
  });
}

interface Suggestion {
  id: string;
  type: string;
  icon: string;
  color: string;
  text: string;
  created_at: string;
}

export function useCopilotSuggestions(interviewId: string, enabled: boolean) {
  return useQuery<{ suggestions: Suggestion[] }>({
    queryKey: ["copilot-suggestions", interviewId],
    queryFn: () =>
      apiFetch(`/api/v1/interviews/${interviewId}/copilot/suggestions`),
    enabled,
    refetchInterval: 5000,
    retry: false,
  });
}

export function useDismissSuggestion(interviewId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (suggestionId: string) =>
      apiFetch(
        `/api/v1/interviews/${interviewId}/copilot/dismiss/${suggestionId}`,
        { method: "POST" }
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: ["copilot-suggestions", interviewId],
      }),
  });
}
