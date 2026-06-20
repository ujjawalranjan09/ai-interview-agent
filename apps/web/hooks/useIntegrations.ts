"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useSlackIntegrations() {
  return useQuery({
    queryKey: ["integrations", "slack"],
    queryFn: () => apiFetch("/api/v1/integrations/slack"),
  });
}

export function useConnectSlack() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { webhook_url: string; channel_name: string; events: string[] }) =>
      apiFetch("/api/v1/integrations/slack", { method: "POST", json: data }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["integrations"] }),
  });
}

export function useDeleteSlack() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch(`/api/v1/integrations/slack/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["integrations"] }),
  });
}

export function useTestSlack() {
  return useMutation({
    mutationFn: (id: string) => apiFetch(`/api/v1/integrations/slack/${id}/test`, { method: "POST" }),
  });
}

export function useTeamsIntegrations() {
  return useQuery({
    queryKey: ["integrations", "teams"],
    queryFn: () => apiFetch("/api/v1/integrations/teams"),
  });
}

export function useConnectTeams() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { webhook_url: string; channel_name: string; events: string[] }) =>
      apiFetch("/api/v1/integrations/teams", { method: "POST", json: data }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["integrations"] }),
  });
}

export function useDeleteTeams() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch(`/api/v1/integrations/teams/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["integrations"] }),
  });
}

export function useTestTeams() {
  return useMutation({
    mutationFn: (id: string) => apiFetch(`/api/v1/integrations/teams/${id}/test`, { method: "POST" }),
  });
}
