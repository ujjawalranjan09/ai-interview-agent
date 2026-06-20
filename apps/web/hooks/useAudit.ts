"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useAuditLogs(filters: {
  action?: string;
  user_id?: string;
  resource_type?: string;
  page?: number;
} = {}) {
  return useQuery<{
    items: {
      id: string;
      user_id: string | null;
      action: string;
      resource_type: string;
      resource_id: string | null;
      details: Record<string, unknown> | null;
      ip_address: string | null;
      created_at: string;
    }[];
    total: number;
    page: number;
    per_page: number;
  }>({
    queryKey: ["audit-logs", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters.action) params.set("action", filters.action);
      if (filters.user_id) params.set("user_id", filters.user_id);
      if (filters.resource_type) params.set("resource_type", filters.resource_type);
      if (filters.page) params.set("page", String(filters.page));
      return apiFetch(`/api/v1/audit/logs?${params}`);
    },
  });
}
