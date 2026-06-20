"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

interface InterviewTemplate {
  id: string;
  name: string;
  description: string | null;
  question_count: number;
  difficulty_level: number;
  question_types: string[];
  skills: string[];
  config: Record<string, unknown> | null;
  is_public: boolean;
  created_by: string;
  created_at: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export function useTemplates(filters?: { page?: number }) {
  return useQuery<PaginatedResponse<InterviewTemplate>>({
    queryKey: ["templates", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.page) params.set("page", String(filters.page));
      return apiFetch(`/api/v1/templates?${params.toString()}`);
    },
  });
}

export function useTemplate(id: string) {
  return useQuery<InterviewTemplate>({
    queryKey: ["template", id],
    queryFn: () => apiFetch(`/api/v1/templates/${id}`),
    enabled: !!id,
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      name: string;
      description?: string;
      question_count?: number;
      difficulty_level?: number;
      question_types?: string[];
      skills?: string[];
      config?: Record<string, unknown>;
      is_public?: boolean;
    }) => apiFetch("/api/v1/templates", { method: "POST", json: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
    },
  });
}

export function useUpdateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; [key: string]: unknown }) =>
      apiFetch(`/api/v1/templates/${id}`, { method: "PATCH", json: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
    },
  });
}

export function useDeleteTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/templates/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
    },
  });
}

export function useCreateInterviewFromTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ templateId, candidateId }: { templateId: string; candidateId: string }) =>
      apiFetch(`/api/v1/templates/${templateId}/create-interview`, {
        method: "POST",
        json: { candidate_id: candidateId },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
    },
  });
}
