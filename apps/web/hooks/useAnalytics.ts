"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useAnalyticsOverview() {
  return useQuery<{
    total_interviews: number;
    completed_interviews: number;
    average_score: number;
    total_candidates: number;
    interviews_this_week: number;
    top_skills: { skill: string; count: number }[];
  }>({
    queryKey: ["analytics-overview"],
    queryFn: () => apiFetch("/api/v1/analytics/overview"),
    staleTime: 60000,
  });
}

export function useCandidateHistory(candidateId: string) {
  return useQuery<{ items: { interview_id: string; date: string; score: number; status: string; question_count: number }[] }>({
    queryKey: ["candidate-history", candidateId],
    queryFn: () => apiFetch(`/api/v1/analytics/candidates/${candidateId}/history`),
    enabled: !!candidateId,
  });
}

export function useAnalyticsTrends() {
  return useQuery<{
    weekly_scores: { week_start: string; average_score: number; interview_count: number }[];
    skill_distribution: { skill: string; count: number }[];
  }>({
    queryKey: ["analytics-trends"],
    queryFn: () => apiFetch("/api/v1/analytics/trends"),
    staleTime: 60000,
  });
}
