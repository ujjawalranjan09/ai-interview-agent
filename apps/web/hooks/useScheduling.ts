"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useAvailability() {
  return useQuery({
    queryKey: ["scheduling", "availability"],
    queryFn: () => apiFetch("/api/v1/scheduling/availability"),
  });
}

export function useSetAvailability() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (slots: { slots: Array<{ day_of_week: number; start_time: string; end_time: string }> }) =>
      apiFetch("/api/v1/scheduling/availability", { method: "PUT", json: slots }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["scheduling", "availability"] }),
  });
}

export function useScheduleInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { interview_id: string; candidate_id: string; scheduled_at: string; duration_minutes?: number; notes?: string }) =>
      apiFetch("/api/v1/scheduling/schedule", { method: "POST", json: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduling", "scheduled"] });
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
    },
  });
}

export function useScheduledInterviews(filters?: { status?: string; page?: number }) {
  return useQuery({
    queryKey: ["scheduling", "scheduled", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.status) params.set("status", filters.status);
      if (filters?.page) params.set("page", String(filters.page));
      return apiFetch(`/api/v1/scheduling/scheduled?${params}`);
    },
  });
}

export function useRescheduleInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; scheduled_at: string; notes?: string }) =>
      apiFetch(`/api/v1/scheduling/scheduled/${id}`, { method: "PUT", json: data }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["scheduling"] }),
  });
}

export function useCancelScheduled() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/scheduling/scheduled/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["scheduling"] }),
  });
}
