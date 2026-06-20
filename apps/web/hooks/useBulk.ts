"use client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useBulkImportCandidates() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (candidates: Array<{ name: string; email?: string; phone?: string; skills?: string[] }>) =>
      apiFetch("/api/v1/bulk/import/candidates", { method: "POST", json: { candidates } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["candidates"] }),
  });
}

export function useBulkUpdateInterviews() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { ids: string[]; updates: Record<string, any> }) =>
      apiFetch("/api/v1/bulk/interviews", { method: "PUT", json: data }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["interviews"] }),
  });
}

export function useBulkDelete() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { entity_type: string; ids: string[] }) =>
      apiFetch("/api/v1/bulk/delete", { method: "POST", json: data }),
    onSuccess: (_, vars) => queryClient.invalidateQueries({ queryKey: [vars.entity_type] }),
  });
}

export function useBulkStatus() {
  return useMutation({
    mutationFn: (data: { entity_type: string; ids: string[] }) =>
      apiFetch("/api/v1/bulk/status", { method: "POST", json: data }),
  });
}
