"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

interface CandidateProfile {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  skills: string[];
  stats: {
    total_interviews: number;
    completed_interviews: number;
    average_score: number;
    best_score: number;
  };
  created_at: string;
}

interface CandidateInterview {
  id: string;
  status: string;
  total_score: number | null;
  questions_answered: number;
  question_count: number;
  start_time: string | null;
  end_time: string | null;
  created_at: string;
}

interface InterviewReport {
  interview_id: string;
  status: string;
  total_score: number | null;
  questions_answered: number;
  question_count: number;
  start_time: string | null;
  end_time: string | null;
  questions: Array<{
    id: string;
    question_text: string;
    question_type: string;
    difficulty: string;
    order_index: number;
    answer: string | null;
    score: number | null;
    semantic_score: number | null;
    keyword_score: number | null;
    concept_score: number | null;
  }>;
  created_at: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export function useCandidateProfile() {
  return useQuery<CandidateProfile>({
    queryKey: ["candidateProfile"],
    queryFn: () => apiFetch("/api/v1/portal/profile"),
  });
}

export function useUpdateCandidateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name?: string; email?: string; phone?: string }) =>
      apiFetch("/api/v1/portal/profile", { method: "PATCH", json: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidateProfile"] });
    },
  });
}

export function useCandidateInterviews(filters?: { page?: number }) {
  return useQuery<PaginatedResponse<CandidateInterview>>({
    queryKey: ["candidateInterviews", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.page) params.set("page", String(filters.page));
      return apiFetch(`/api/v1/portal/interviews?${params.toString()}`);
    },
  });
}

export function useInterviewReport(interviewId: string) {
  return useQuery<InterviewReport>({
    queryKey: ["interviewReport", interviewId],
    queryFn: () => apiFetch(`/api/v1/portal/interviews/${interviewId}/report`),
    enabled: !!interviewId,
  });
}
