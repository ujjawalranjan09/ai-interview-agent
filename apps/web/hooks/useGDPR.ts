"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

interface Consent {
  id: string;
  consent_type: string;
  granted: boolean;
  granted_at: string | null;
  revoked_at: string | null;
}

export function useConsents() {
  return useQuery<Consent[]>({
    queryKey: ["gdpr", "consents"],
    queryFn: () => apiFetch("/api/v1/gdpr/consents"),
  });
}

export function useUpdateConsent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { consent_type: string; granted: boolean }) =>
      apiFetch("/api/v1/gdpr/consents", { method: "PUT", json: data }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["gdpr", "consents"] }),
  });
}

export function useDataExport() {
  return useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/gdpr/export", { method: "POST" }),
  });
}

export function useExportStatus() {
  return useQuery({
    queryKey: ["gdpr", "exports"],
    queryFn: () => apiFetch("/api/v1/gdpr/export"),
  });
}

export function useDeleteData() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/gdpr/data", { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gdpr"] });
    },
  });
}

export function useRetentionPolicies() {
  return useQuery({
    queryKey: ["gdpr", "retention"],
    queryFn: () => apiFetch("/api/v1/gdpr/retention"),
  });
}

export function useUpdateRetention() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { entity_type: string; retention_days: number; auto_delete?: boolean }) =>
      apiFetch("/api/v1/gdpr/retention", { method: "PUT", json: data }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["gdpr", "retention"] }),
  });
}
