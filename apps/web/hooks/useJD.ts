"use client";

import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useJdMatch(candidateId: string) {
  return useMutation({
    mutationFn: (data: { jd_text: string }) =>
      apiFetch(`/api/v1/candidates/${candidateId}/jd`, {
        method: "POST",
        json: data,
      }),
  });
}

export function useJdQuestions(candidateId: string) {
  return useMutation({
    mutationFn: (data: { jd_text: string; count?: number }) =>
      apiFetch(`/api/v1/candidates/${candidateId}/jd/questions`, {
        method: "POST",
        json: data,
      }),
  });
}
