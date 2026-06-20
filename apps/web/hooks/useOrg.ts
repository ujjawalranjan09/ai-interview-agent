"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

interface Organization {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  logo_url: string | null;
  website: string | null;
  industry: string | null;
  size: string | null;
  settings: Record<string, unknown> | null;
  is_active: boolean;
  member_count: number;
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

export function useOrganizations(filters?: { page?: number }) {
  return useQuery<PaginatedResponse<Organization>>({
    queryKey: ["organizations", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.page) params.set("page", String(filters.page));
      return apiFetch(`/api/v1/organizations?${params.toString()}`);
    },
  });
}

export function useOrganization(id: string) {
  return useQuery<Organization>({
    queryKey: ["organization", id],
    queryFn: () => apiFetch(`/api/v1/organizations/${id}`),
    enabled: !!id,
  });
}

export function useCreateOrganization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      name: string;
      description?: string;
      website?: string;
      industry?: string;
      size?: string;
    }) => apiFetch("/api/v1/organizations", { method: "POST", json: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organizations"] });
    },
  });
}

export function useUpdateOrganization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; [key: string]: unknown }) =>
      apiFetch(`/api/v1/organizations/${id}`, { method: "PATCH", json: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organizations"] });
    },
  });
}

export function useDeleteOrganization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/organizations/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organizations"] });
    },
  });
}
