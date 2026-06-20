"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useReport(interviewId: string) {
  return useQuery({
    queryKey: ["report", interviewId],
    queryFn: () => apiFetch(`/api/v1/interviews/${interviewId}/report`),
    enabled: !!interviewId,
    retry: false,
  });
}

export function useGenerateReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (interviewId: string) =>
      apiFetch(`/api/v1/interviews/${interviewId}/report/generate`, { method: "POST" }),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ["report", id] });
      qc.invalidateQueries({ queryKey: ["interview", id] });
    },
  });
}

export function useCoachingPlan(interviewId: string) {
  return useQuery({
    queryKey: ["coaching", interviewId],
    queryFn: () => apiFetch(`/api/v1/interviews/${interviewId}/coaching`),
    enabled: !!interviewId,
    retry: false,
  });
}

export function useGenerateCoaching() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ interviewId, force }: { interviewId: string; force?: boolean }) =>
      apiFetch(`/api/v1/interviews/${interviewId}/coaching/generate${force ? "?force=true" : ""}`, { method: "POST" }),
    onSuccess: (_, { interviewId }) => {
      qc.invalidateQueries({ queryKey: ["coaching", interviewId] });
      qc.invalidateQueries({ queryKey: ["interview", interviewId] });
    },
  });
}

export function useReplayData(interviewId: string) {
  return useQuery({
    queryKey: ["replay", interviewId],
    queryFn: () => apiFetch(`/api/v1/interviews/${interviewId}/replay`),
    enabled: !!interviewId,
    retry: false,
  });
}
