"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useAdminUsers(filters: { role?: string; page?: number } = {}) {
  return useQuery<{
    items: {
      id: string;
      email: string;
      full_name: string;
      role: string;
      is_active: boolean;
      created_at: string;
    }[];
    total: number;
    page: number;
    per_page: number;
  }>({
    queryKey: ["admin-users", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters.role) params.set("role", filters.role);
      if (filters.page) params.set("page", String(filters.page));
      return apiFetch(`/api/v1/admin/users?${params}`);
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      userId,
      ...data
    }: {
      userId: string;
      role?: string;
      is_active?: boolean;
    }) =>
      apiFetch(`/api/v1/admin/users/${userId}`, {
        method: "PATCH",
        json: data,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });
}

export function useSystemHealth() {
  return useQuery<{ status: string; database: string; timestamp: string }>({
    queryKey: ["system-health"],
    queryFn: () => apiFetch("/api/v1/admin/system/health"),
    refetchInterval: 30000,
  });
}

export function useSystemStats() {
  return useQuery<{
    total_users: number;
    total_interviews: number;
    total_candidates: number;
    active_sessions: number;
  }>({
    queryKey: ["system-stats"],
    queryFn: () => apiFetch("/api/v1/admin/system/stats"),
    staleTime: 30000,
  });
}
