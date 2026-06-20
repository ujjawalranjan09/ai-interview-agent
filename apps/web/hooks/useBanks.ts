"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

interface QuestionBank {
  id: string;
  name: string;
  description: string | null;
  category: string;
  question_count: number;
  is_public: boolean;
  created_by: string;
  created_at: string;
}

interface BankQuestion {
  id: string;
  bank_id: string;
  question_text: string;
  question_type: string;
  difficulty: string;
  reference_answer: string | null;
  keywords: string[] | null;
  concepts: string[] | null;
  tags: string[];
  source_interview_id: string | null;
  created_at: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export function useBanks(filters?: { category?: string; page?: number }) {
  return useQuery<PaginatedResponse<QuestionBank>>({
    queryKey: ["banks", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.category) params.set("category", filters.category);
      if (filters?.page) params.set("page", String(filters.page));
      return apiFetch(`/api/v1/banks?${params.toString()}`);
    },
  });
}

export function useBank(id: string) {
  return useQuery<QuestionBank>({
    queryKey: ["bank", id],
    queryFn: () => apiFetch(`/api/v1/banks/${id}`),
    enabled: !!id,
  });
}

export function useCreateBank() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; description?: string; category: string; is_public?: boolean }) =>
      apiFetch("/api/v1/banks", { method: "POST", json: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["banks"] });
    },
  });
}

export function useDeleteBank() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/banks/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["banks"] });
    },
  });
}

export function useBankQuestions(
  bankId: string,
  filters?: { page?: number; difficulty?: string; question_type?: string }
) {
  return useQuery<PaginatedResponse<BankQuestion>>({
    queryKey: ["bankQuestions", bankId, filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.page) params.set("page", String(filters.page));
      if (filters?.difficulty) params.set("difficulty", filters.difficulty);
      if (filters?.question_type) params.set("question_type", filters.question_type);
      return apiFetch(`/api/v1/banks/${bankId}/questions?${params.toString()}`);
    },
    enabled: !!bankId,
  });
}

export function useAddBankQuestion(bankId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      question_text: string;
      question_type: string;
      difficulty: string;
      reference_answer?: string;
      keywords?: string[];
      concepts?: string[];
      tags?: string[];
    }) =>
      apiFetch(`/api/v1/banks/${bankId}/questions`, { method: "POST", json: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bankQuestions", bankId] });
      queryClient.invalidateQueries({ queryKey: ["bank", bankId] });
    },
  });
}

export function useImportFromInterview(bankId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (interviewId: string) =>
      apiFetch(`/api/v1/banks/${bankId}/import/${interviewId}`, { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bankQuestions", bankId] });
      queryClient.invalidateQueries({ queryKey: ["bank", bankId] });
    },
  });
}

export function useGenerateInterviewFromBank(bankId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { candidate_id: string; count?: number; difficulty?: string }) =>
      apiFetch(`/api/v1/banks/${bankId}/generate-interview`, {
        method: "POST",
        json: data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
    },
  });
}
