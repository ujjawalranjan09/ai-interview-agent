"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function usePlagiarismChecks(submissionId?: string) {
  return useQuery({
    queryKey: ["plagiarism", "checks", submissionId],
    queryFn: () => {
      const params = new URLSearchParams();
      if (submissionId) params.set("submission_id", submissionId);
      return apiFetch(`/api/v1/plagiarism/checks?${params}`);
    },
    enabled: !!submissionId,
  });
}

export function useCreatePlagiarismCheck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (submissionId: string) =>
      apiFetch("/api/v1/plagiarism/checks", { method: "POST", json: { submission_id: submissionId } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["plagiarism"] }),
  });
}

export function useRunAnalysis() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (checkId: string) =>
      apiFetch(`/api/v1/plagiarism/checks/${checkId}/analyze`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["plagiarism"] }),
  });
}

export function usePlagiarismCheck(checkId?: string) {
  return useQuery({
    queryKey: ["plagiarism", "check", checkId],
    queryFn: () => apiFetch(`/api/v1/plagiarism/checks/${checkId}`),
    enabled: !!checkId,
  });
}
