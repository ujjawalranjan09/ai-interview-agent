"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

interface Webhook {
  id: string;
  name: string;
  url: string;
  events: string[];
  is_active: boolean;
  failure_count: number;
  last_triggered_at: string | null;
  last_status: string | null;
  created_at: string;
}

interface WebhookDelivery {
  id: string;
  webhook_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  response_status: number | null;
  response_body: string | null;
  success: boolean;
  error_message: string | null;
  attempts: number;
  created_at: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export function useWebhooks(filters?: { page?: number }) {
  return useQuery<PaginatedResponse<Webhook>>({
    queryKey: ["webhooks", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.page) params.set("page", String(filters.page));
      return apiFetch(`/api/v1/webhooks?${params.toString()}`);
    },
  });
}

export function useWebhook(id: string) {
  return useQuery<Webhook>({
    queryKey: ["webhook", id],
    queryFn: () => apiFetch(`/api/v1/webhooks/${id}`),
    enabled: !!id,
  });
}

export function useCreateWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; url: string; events: string[]; secret?: string }) =>
      apiFetch("/api/v1/webhooks", { method: "POST", json: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
  });
}

export function useUpdateWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; [key: string]: unknown }) =>
      apiFetch(`/api/v1/webhooks/${id}`, { method: "PATCH", json: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
  });
}

export function useDeleteWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/webhooks/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
  });
}

export function useTestWebhook() {
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/webhooks/${id}/test`, { method: "POST" }),
  });
}

export function useWebhookDeliveries(webhookId: string, filters?: { page?: number }) {
  return useQuery<PaginatedResponse<WebhookDelivery>>({
    queryKey: ["webhookDeliveries", webhookId, filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.page) params.set("page", String(filters.page));
      return apiFetch(`/api/v1/webhooks/${webhookId}/deliveries?${params.toString()}`);
    },
    enabled: !!webhookId,
  });
}
