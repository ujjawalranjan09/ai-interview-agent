"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

interface CodingQuestion {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  category: string;
  language: string;
  starter_code: string | null;
  solution: string | null;
  test_cases: Array<{ input: unknown; expected: unknown }> | null;
  constraints: string | null;
  examples: Array<{ input: string; output: string; explanation?: string }> | null;
  tags: string[];
  created_at: string;
}



interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export function useCodingQuestions(filters?: {
  difficulty?: string;
  category?: string;
  page?: number;
}) {
  return useQuery<PaginatedResponse<CodingQuestion>>({
    queryKey: ["codingQuestions", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.difficulty) params.set("difficulty", filters.difficulty);
      if (filters?.category) params.set("category", filters.category);
      if (filters?.page) params.set("page", String(filters.page));
      return apiFetch(`/api/v1/coding/questions?${params.toString()}`);
    },
  });
}

export function useCodingQuestion(id: string) {
  return useQuery<CodingQuestion>({
    queryKey: ["codingQuestion", id],
    queryFn: () => apiFetch(`/api/v1/coding/questions/${id}`),
    enabled: !!id,
  });
}

export function useCreateCodingQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      title: string;
      description: string;
      difficulty: string;
      category: string;
      language?: string;
      starter_code?: string;
      solution?: string;
      test_cases?: Array<{ input: unknown; expected: unknown }>;
      constraints?: string;
      examples?: Array<{ input: string; output: string; explanation?: string }>;
      tags?: string[];
    }) => apiFetch("/api/v1/coding/questions", { method: "POST", json: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["codingQuestions"] });
    },
  });
}

export function useSubmitCode() {
  return useMutation({
    mutationFn: ({
      questionId,
      code,
      language,
    }: {
      questionId: string;
      code: string;
      language: string;
    }) =>
      apiFetch(`/api/v1/coding/questions/${questionId}/submit`, {
        method: "POST",
        json: { code, language },
      }),
  });
}

export function useDeleteCodingQuestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/coding/questions/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["codingQuestions"] });
    },
  });
}
