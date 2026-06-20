"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useScreenCandidate(candidateId?: string) {
  return useMutation({
    mutationFn: (data: { job_description: string }) =>
      apiFetch(`/api/v1/screening/candidates/${candidateId}`, { method: "POST", json: data }),
  });
}

export function useRankCandidates() {
  return useMutation({
    mutationFn: (data: { job_description: string; candidate_ids: string[] }) =>
      apiFetch("/api/v1/screening/rank", { method: "POST", json: data }),
  });
}

export function useScreeningHistory(candidateId?: string) {
  return useQuery({
    queryKey: ["screening", "history", candidateId],
    queryFn: () => apiFetch(`/api/v1/screening/candidates/${candidateId}/history`),
    enabled: !!candidateId,
  });
}
