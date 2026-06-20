"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

interface Interview {
  id: string;
  candidate_id: string;
  interviewer_id: string | null;
  status: string;
  difficulty_level: number;
  question_count: number;
  questions_answered: number;
  total_score: number;
  start_time: string | null;
  end_time: string | null;
  created_at: string;
  config: Record<string, unknown> | null;
}

interface Question {
  id: string;
  question_text: string;
  question_type: string;
  difficulty: string;
  order_index: number;
  candidate_answer_text: string | null;
  answer_score: number;
  semantic_score: number;
  keyword_score: number;
  concept_score: number;
  follow_up_of: string | null;
  created_at: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export function useInterviews(filters?: { status?: string; candidate_id?: string; page?: number }) {
  return useQuery<PaginatedResponse<Interview>>({
    queryKey: ["interviews", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.status) params.set("status", filters.status);
      if (filters?.candidate_id) params.set("candidate_id", filters.candidate_id);
      if (filters?.page) params.set("page", String(filters.page));
      return apiFetch(`/api/v1/interviews?${params}`);
    },
  });
}

export function useInterview(id: string) {
  return useQuery<Interview>({
    queryKey: ["interview", id],
    queryFn: () => apiFetch(`/api/v1/interviews/${id}`),
    enabled: !!id,
  });
}

export function useInterviewQuestions(interviewId: string) {
  return useQuery<Question[]>({
    queryKey: ["questions", interviewId],
    queryFn: () => apiFetch(`/api/v1/interviews/${interviewId}/questions`),
    enabled: !!interviewId,
  });
}

export function useCreateInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { candidate_id: string; question_count?: number; difficulty_level?: number }) =>
      apiFetch<Interview>("/api/v1/interviews", { method: "POST", json: data }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["interviews"] }),
  });
}

export function useStartInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch<Interview>(`/api/v1/interviews/${id}/start`, { method: "POST" }),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
      queryClient.invalidateQueries({ queryKey: ["interview", id] });
      queryClient.invalidateQueries({ queryKey: ["questions", id] });
    },
  });
}

export function useSubmitAnswer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ questionId, answer_text }: { questionId: string; answer_text: string }) =>
      apiFetch<{ total_score: number; semantic_score: number; keyword_score: number; concept_score: number; feedback?: string }>(
        `/api/v1/questions/${questionId}/answer`,
        { method: "POST", json: { answer_text } },
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["questions"] }),
  });
}

export function useRequestFollowup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (questionId: string) =>
      apiFetch<Question>(`/api/v1/questions/${questionId}/followup`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["questions"] }),
  });
}

export function useCloseInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch<Interview>(`/api/v1/interviews/${id}/close`, { method: "POST" }),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
      queryClient.invalidateQueries({ queryKey: ["interview", id] });
    },
  });
}

export function useSubmitAudioAnswer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ questionId, blob }: { questionId: string; blob: Blob }) => {
      const formData = new FormData();
      formData.append("file", blob, "recording.webm");

      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

      const getAuthHeaders = (): Record<string, string> => {
        const tokens = sessionStorage.getItem("auth-tokens");
        if (tokens) {
          const parsed = JSON.parse(tokens);
          if (parsed.accessToken) return { Authorization: `Bearer ${parsed.accessToken}` };
        }
        return {};
      };

      const doUpload = async (headers: Record<string, string>) => {
        return fetch(`${API_URL}/api/v1/questions/${questionId}/answer-audio`, {
          method: "POST",
          headers,
          body: formData,
        });
      };

      let headers = getAuthHeaders();
      let response = await doUpload(headers);

      // Handle 401 with token refresh retry
      if (response.status === 401) {
        const tokens = sessionStorage.getItem("auth-tokens");
        if (tokens) {
          const parsed = JSON.parse(tokens);
          if (parsed.refreshToken) {
            const refreshResponse = await fetch(`${API_URL}/api/v1/auth/refresh`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ refresh_token: parsed.refreshToken }),
            });
            if (refreshResponse.ok) {
              const newTokens = await refreshResponse.json();
              const newStored = { accessToken: newTokens.access_token, refreshToken: newTokens.refresh_token };
              sessionStorage.setItem("auth-tokens", JSON.stringify(newStored));
              document.cookie = `auth-token=${newStored.accessToken}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Lax`;
              headers = { Authorization: `Bearer ${newStored.accessToken}` };
              response = await doUpload(headers);
            }
          }
        }
      }

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(err.detail || "Upload failed");
      }

      const result = await response.json();

      // If async (task processing), poll until complete
      if (result.status === "processing") {
        for (let i = 0; i < 60; i++) {
          await new Promise((r) => setTimeout(r, 2000));
          const statusResponse = await fetch(
            `${API_URL}/api/v1/questions/${questionId}/task-status`,
            { headers },
          );
          const statusData = await statusResponse.json();
          if (statusData.has_answer) {
            // Fetch the updated question to get scores
            const qResponse = await fetch(
              `${API_URL}/api/v1/questions/${questionId}`,
              { headers },
            );
            const q = await qResponse.json();
            queryClient.invalidateQueries({ queryKey: ["questions"] });
            return {
              total_score: q.answer_score,
              semantic_score: q.semantic_score,
              keyword_score: q.keyword_score,
              concept_score: q.concept_score,
            };
          }
        }
        throw new Error("Transcription timed out");
      }

      // Sync response
      queryClient.invalidateQueries({ queryKey: ["questions"] });
      return result.evaluation || result;
    },
  });
}
