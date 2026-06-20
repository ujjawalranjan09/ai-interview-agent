"use client";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

interface SearchResult {
  id: string;
  type: "candidate" | "interview" | "question" | "bank";
  title: string;
  subtitle: string;
  link: string;
}

interface SearchResponse {
  [key: string]: SearchResult[] | number;
  total: number;
}

export function useSearch(query: string, type?: string) {
  return useQuery<SearchResponse>({
    queryKey: ["search", query, type],
    queryFn: async () => {
      const params = new URLSearchParams({ q: query });
      if (type) params.set("type", type);
      return apiFetch(`/api/v1/search?${params}`);
    },
    enabled: query.length >= 2,
    staleTime: 30_000,
  });
}
