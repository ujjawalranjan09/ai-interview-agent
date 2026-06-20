"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

interface BrandingData {
  logo_url?: string;
  favicon_url?: string;
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  font_family?: string;
  custom_css?: string;
  custom_domain?: string;
  email_template?: string;
  portal_heading?: string;
  theme_config?: Record<string, any>;
}

export function useBranding() {
  return useQuery({
    queryKey: ["branding"],
    queryFn: () => apiFetch("/api/v1/branding"),
  });
}

export function useUpdateBranding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: BrandingData) =>
      apiFetch("/api/v1/branding", { method: "PUT", json: data }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["branding"] }),
  });
}
