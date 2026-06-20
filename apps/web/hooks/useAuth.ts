"use client";

import { useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  avatar_url: string | null;
  is_active: boolean;
  created_at: string;
}

export function useAuth() {
  const { user, setUser, setTokens, logout, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: userData, isLoading } = useQuery<User>({
    queryKey: ["me"],
    queryFn: () => apiFetch<User>("/api/v1/auth/me"),
    enabled: isAuthenticated,
    retry: false,
  });

  // Sync fetched user data to store (in useEffect to avoid render-time side effects)
  useEffect(() => {
    if (userData && !user) {
      setUser(userData);
    }
  }, [userData, user, setUser]);

  const loginMutation = useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      apiFetch<{ access_token: string; refresh_token: string }>("/api/v1/auth/login", {
        method: "POST",
        json: data,
      }),
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token);
      queryClient.invalidateQueries({ queryKey: ["me"] });
      router.push("/");
    },
  });

  const registerMutation = useMutation({
    mutationFn: (data: {
      email: string;
      password: string;
      full_name: string;
      role?: string;
    }) =>
      apiFetch<{ access_token: string; refresh_token: string }>("/api/v1/auth/register", {
        method: "POST",
        json: data,
      }),
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token);
      queryClient.invalidateQueries({ queryKey: ["me"] });
      router.push("/");
    },
  });

  const handleLogout = () => {
    logout();
    queryClient.clear();
    router.push("/");
  };

  return {
    user: userData || user,
    isLoading,
    isAuthenticated,
    login: loginMutation,
    register: registerMutation,
    logout: handleLogout,
  };
}
